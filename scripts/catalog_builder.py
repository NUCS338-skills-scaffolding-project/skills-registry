#!/usr/bin/env python3
"""
catalog_builder.py — Mentora skills-registry catalog builder

Walks team repos (locally or via the GitHub API), reads each skills.md,
parses frontmatter and body sections, validates against the v1 contract,
and writes catalog.json + a human-readable build report + a changelog.

See Mentora-Orchestrator-Catalog-Contract-v0.1.md for the full schema.

Modes:
  - github (default): walks an org's team repos via the GitHub API.
                      Requires GITHUB_TOKEN and GITHUB_ORG env vars.
  - local: walks a local directory whose subdirs are team repos.
           Triggered with --local <path>.

Usage:
  python catalog_builder.py
  python catalog_builder.py --local /path/to/parent/dir
  python catalog_builder.py --local . --output catalog.json --report build_report.md
  python catalog_builder.py --strict          # exit 1 if any skill is broken
  python catalog_builder.py --changelog catalog_changelog.json
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import requests
import yaml


# ---------------------------------------------------------------------------
# Tiny inline frontmatter parser (no python-frontmatter dependency)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)

def parse_frontmatter(text: str) -> tuple:
    """Return (metadata_dict, body_str). Raises yaml.YAMLError on bad YAML."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise yaml.YAMLError("frontmatter is not a YAML mapping")
    return meta, m.group(2)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_SKILL_TYPES = {"instructional", "code"}
VALID_STANCES = {"socratic", "hint", "reframe", "meta"}
VALID_COURSE_TYPES = {"cs", "humanities"}
SKILL_ID_MAX_LEN = 18
SKIP_REPOS = {"skills-registry", "skill-standard-template"}

# Catalog schema version — bump according to SCHEMA_COMPAT.md policy:
#   - Patch: new optional output fields added (backwards-compatible)
#   - Minor: existing fields renamed (deprecated old name kept for 1 release cycle)
#   - Major: breaking change — orchestrator must be updated before deploying new registry
CATALOG_SCHEMA_VERSION = "1.0.0"

INSTRUCTIONAL_BODY_SECTIONS = {
    "description", "when_to_trigger", "tutor_stance", "flow",
    "safe_output_types", "must_avoid", "example_exchange",
}
CODE_BODY_SECTIONS = {
    "description", "when_to_trigger", "inputs", "outputs", "usage", "notes",
}

# Fields compared when computing the changelog between two catalog builds
CHANGELOG_TRACKED_FIELDS = [
    "status", "version", "name", "skill_type", "stance",
    "owner_team", "owner_contact", "source_repo",
]


# ---------------------------------------------------------------------------
# Repo handle abstraction — unifies local-dir and GitHub-API access
# ---------------------------------------------------------------------------

@dataclass
class RepoHandle:
    name: str
    read: Callable[[str], Optional[str]]      # read(rel_path) -> text or None
    exists: Callable[[str], bool]
    list_files: Callable[[str], list]         # list paths under a prefix
    source_url_base: Optional[str] = None     # GitHub URL base, or None


# ---------- Local mode ----------

def discover_local_repos(root: Path) -> list:
    repos = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith(".") or child.name in SKIP_REPOS:
            continue
        repos.append(_local_repo_handle(child))
    return repos

def _local_repo_handle(repo_root: Path) -> RepoHandle:
    def read(rel: str):
        p = repo_root / rel
        return p.read_text(encoding="utf-8") if p.is_file() else None
    def exists(rel: str) -> bool:
        return (repo_root / rel).exists()
    def list_files(prefix: str):
        base = repo_root / prefix
        if not base.is_dir():
            return []
        return sorted(
            str(p.relative_to(repo_root)).replace(os.sep, "/")
            for p in base.rglob("*") if p.is_file()
        )
    return RepoHandle(name=repo_root.name, read=read, exists=exists, list_files=list_files)


# ---------- GitHub mode ----------

def discover_github_repos(org: str, token: str) -> list:
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    repos, page = [], 1
    while True:
        r = requests.get(f"https://api.github.com/orgs/{org}/repos",
                         headers=headers, params={"page": page, "per_page": 100})
        if r.status_code != 200:
            print(f"ERROR: GitHub API {r.status_code}: {r.text[:200]}", file=sys.stderr)
            break
        data = r.json()
        if not data:
            break
        for repo in data:
            if repo["name"] in SKIP_REPOS:
                continue
            repos.append(_github_repo_handle(org, repo["name"], headers))
        page += 1
    return repos

def _github_repo_handle(org: str, name: str, headers: dict) -> RepoHandle:
    cache = {"tree": None}
    def _tree():
        if cache["tree"] is None:
            r = requests.get(
                f"https://api.github.com/repos/{org}/{name}/git/trees/main?recursive=1",
                headers=headers,
            )
            cache["tree"] = r.json().get("tree", []) if r.status_code == 200 else []
        return cache["tree"]

    def read(rel: str):
        r = requests.get(f"https://api.github.com/repos/{org}/{name}/contents/{rel}",
                         headers=headers)
        if r.status_code != 200:
            return None
        try:
            return base64.b64decode(r.json()["content"]).decode("utf-8")
        except Exception:
            return None
    def exists(rel: str) -> bool:
        return any(item["path"] == rel for item in _tree())
    def list_files(prefix: str):
        return [item["path"] for item in _tree()
                if item.get("type") == "blob" and item["path"].startswith(prefix)]

    return RepoHandle(
        name=name, read=read, exists=exists, list_files=list_files,
        source_url_base=f"https://github.com/{org}/{name}/tree/main",
    )


# ---------------------------------------------------------------------------
# Body parsing — splits markdown body into structured sections
# ---------------------------------------------------------------------------

def _normalize_heading(h: str) -> str:
    h = h.strip().lower()
    h = re.sub(r"[^a-z0-9]+", "_", h)
    return h.strip("_")

def parse_body_sections(body: str) -> dict:
    """Split markdown body into sections by ## headings."""
    sections, current_key, lines = {}, None, []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current_key is not None:
                sections[current_key] = "\n".join(lines).strip()
            current_key = _normalize_heading(m.group(1))
            lines = []
        elif current_key is not None:
            lines.append(line)
    if current_key is not None:
        sections[current_key] = "\n".join(lines).strip()
    return sections

def parse_flow(text: str) -> list:
    """Parse a Flow section into [{step, title, description}, ...]."""
    if not text:
        return []
    steps, current, current_lines, n = [], None, [], 0
    for line in text.splitlines():
        m = re.match(r"^###\s+(?:Step\s+(\d+)\s*[-—:]\s*)?(.*?)\s*$", line)
        if m:
            if current is not None:
                current["description"] = "\n".join(current_lines).strip()
                steps.append(current)
            n += 1
            num = int(m.group(1)) if m.group(1) else n
            title = (m.group(2) or "").strip() or f"Step {num}"
            current, current_lines = {"step": num, "title": title, "description": ""}, []
        elif current is not None:
            current_lines.append(line)
    if current is not None:
        current["description"] = "\n".join(current_lines).strip()
        steps.append(current)
    return steps

def parse_bullet_list(text: str) -> list:
    """Parse bullet markdown into a list of strings."""
    if not text:
        return []
    items = [m.group(1).strip()
             for line in text.splitlines()
             if (m := re.match(r"^\s*[-*+]\s+(.+?)\s*$", line))]
    if items:
        return items
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paras


# ---------------------------------------------------------------------------
# Skill loading — frontmatter + body parsing → flat dict
# ---------------------------------------------------------------------------

def load_skill_from_path(repo: RepoHandle, skills_md_path: str) -> Optional[dict]:
    raw = repo.read(skills_md_path)
    if raw is None:
        return None
    try:
        meta, body = parse_frontmatter(raw)
    except Exception as e:
        return {"_parse_error": str(e), "source_repo": repo.name, "source_path": skills_md_path}

    skill = dict(meta)
    sections = parse_body_sections(body)

    skill["description"] = sections.get("description") or None
    skill["trigger_summary"] = sections.get("when_to_trigger") or None

    if skill.get("skill_type") == "instructional":
        ts = sections.get("tutor_stance", "")
        skill["tutor_stance_rules"] = parse_bullet_list(ts) or ([ts.strip()] if ts.strip() else [])
        skill["flow"] = parse_flow(sections.get("flow", ""))
        so = sections.get("safe_output_types", "")
        skill["safe_outputs"] = parse_bullet_list(so) or ([so.strip()] if so.strip() else [])
        ma = sections.get("must_avoid", "")
        skill["must_avoid"] = parse_bullet_list(ma) or ([ma.strip()] if ma.strip() else [])
        skill["example_exchange"] = sections.get("example_exchange") or None
    elif skill.get("skill_type") == "code":
        skill["inputs_schema_text"] = sections.get("inputs") or None
        skill["outputs_schema_text"] = sections.get("outputs") or None
        skill["usage_example"] = sections.get("usage") or None
        skill["code_notes"] = sections.get("notes") or None

    known = INSTRUCTIONAL_BODY_SECTIONS | CODE_BODY_SECTIONS
    extras = {k: v for k, v in sections.items() if k not in known}
    if extras:
        skill["extra_sections"] = extras

    skill["source_repo"] = repo.name
    skill["source_path"] = skills_md_path
    if repo.source_url_base:
        skill["source_url"] = f"{repo.source_url_base}/{skills_md_path}"
    return skill


# ---------------------------------------------------------------------------
# Validation — produces (status, reason, issues)
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    severity: str           # "error" | "warning"
    field: str
    message: str

def validate_skill(skill: dict) -> tuple:
    issues = []
    if "_parse_error" in skill:
        issues.append(Issue("error", "skills.md", f"frontmatter parse error: {skill['_parse_error']}"))
        return "broken", "skills.md unparseable", issues

    skill_type = skill.get("skill_type")

    if not skill.get("skill_id"):
        issues.append(Issue("error", "skill_id", "missing"))
    if not skill.get("name"):
        issues.append(Issue("error", "name", "missing"))
    if skill_type not in VALID_SKILL_TYPES:
        issues.append(Issue("error", "skill_type", f"must be one of {sorted(VALID_SKILL_TYPES)}"))
    if not skill.get("tags"):
        issues.append(Issue("error", "tags", "missing or empty"))

    course_types = skill.get("course_types") or []
    if not course_types:
        issues.append(Issue("error", "course_types",
                             "missing or empty (must be subset of cs/humanities)"))
    else:
        bad = [ct for ct in course_types if ct not in VALID_COURSE_TYPES]
        if bad:
            issues.append(Issue("error", "course_types", f"invalid values: {bad}"))

    if not skill.get("learning_goal_tags"):
        issues.append(Issue("warning", "learning_goal_tags",
                             "missing — strongly recommended for orchestrator routing"))

    if skill_type == "instructional":
        if skill.get("stance") not in VALID_STANCES:
            issues.append(Issue("error", "stance", f"must be one of {sorted(VALID_STANCES)}"))
        for fld, label, msg in [
            ("description", "description", "add a `## Description` section"),
            ("trigger_summary", "when_to_trigger", "add a `## When to Trigger` section"),
            ("tutor_stance_rules", "tutor_stance", "add a `## Tutor Stance` section with rules"),
            ("flow", "flow", "add a `## Flow` section with `### Step N` subsections"),
            ("safe_outputs", "safe_output_types", "add a `## Safe Output Types` section"),
            ("must_avoid", "must_avoid", "add a `## Must Avoid` section"),
        ]:
            if not skill.get(fld):
                issues.append(Issue("error", label, f"missing — {msg}"))
        if not skill.get("example_exchange"):
            issues.append(Issue("warning", "example_exchange", "missing — strongly recommended"))

    elif skill_type == "code":
        if skill.get("stance"):
            issues.append(Issue("warning", "stance",
                                 "stance is for instructional skills only; remove for code"))
        for fld, label, msg in [
            ("description", "description", "add `## Description` section"),
            ("trigger_summary", "when_to_trigger", "add `## When to Trigger` section"),
            ("inputs_schema_text", "inputs", "add `## Inputs` section"),
            ("outputs_schema_text", "outputs", "add `## Outputs` section"),
            ("usage_example", "usage", "add `## Usage` section"),
        ]:
            if not skill.get(fld):
                issues.append(Issue("error", label, f"missing — {msg}"))

    sid = skill.get("skill_id") or ""
    if len(sid) > SKILL_ID_MAX_LEN:
        issues.append(Issue("warning", "skill_id",
                             f"length {len(sid)} > {SKILL_ID_MAX_LEN} chars — see Team-Guide §7"))
    nm = (skill.get("name") or "").strip()
    if nm.lower().endswith(" skill"):
        issues.append(Issue("warning", "name",
                             "ends with 'Skill' — drop the suffix per Team-Guide §7"))

    has_errors = any(i.severity == "error" for i in issues)
    if not has_errors:
        return "ready", None, issues
    if skill.get("owner_team"):
        reason = "; ".join(i.message for i in issues if i.severity == "error")
        return "stub", reason, issues
    return "broken", "missing required fields and no owning team", issues


# ---------------------------------------------------------------------------
# Build pass — with skill_id uniqueness enforcement (B2.3)
# ---------------------------------------------------------------------------

@dataclass
class BuildResult:
    catalog: list = field(default_factory=list)
    issues_by_skill: dict = field(default_factory=dict)
    duplicate_rejections: list = field(default_factory=list)


def build_catalog(repos: list) -> BuildResult:
    result = BuildResult()
    seen_ids: dict[str, str] = {}  # skill_id → first source_repo that claimed it

    for repo in repos:
        meta = {}
        meta_text = repo.read("metadata.yaml")
        if meta_text:
            try:
                meta = yaml.safe_load(meta_text) or {}
            except Exception:
                meta = {}
        owner_team = meta.get("course_id") or repo.name
        owner_contact = meta.get("spoc_contact")

        skills_paths = [p for p in repo.list_files("skills") if p.endswith("/skills.md")]
        if not skills_paths:
            continue

        for path in skills_paths:
            print(f"  scanning {repo.name}/{path}", file=sys.stderr)
            skill = load_skill_from_path(repo, path)
            if skill is None:
                continue
            skill["owner_team"] = owner_team
            skill["owner_contact"] = owner_contact

            # ── B2.3: skill_id uniqueness enforcement ──────────────────────
            # First repo to register a slug wins; the second is rejected with
            # a clear error message surfaced both to stderr and the build report.
            skill_id = skill.get("skill_id", "")
            if skill_id and skill_id in seen_ids:
                first_repo = seen_ids[skill_id]
                dup_msg = (
                    f"skill_id '{skill_id}' is already claimed by repo '{first_repo}'. "
                    f"Repo '{repo.name}' is rejected. "
                    f"Rename this skill or coordinate with the '{first_repo}' team."
                )
                dup_issue = Issue("error", "skill_id", dup_msg)
                skill["status"] = "broken"
                skill["status_reason"] = dup_msg
                result.catalog.append(skill)
                result.issues_by_skill[f"{repo.name}/{path}"] = [dup_issue]
                result.duplicate_rejections.append({
                    "skill_id": skill_id,
                    "rejected_repo": repo.name,
                    "rejected_path": path,
                    "first_claimed_by": first_repo,
                })
                print(
                    f"  ERROR: duplicate skill_id '{skill_id}' — "
                    f"'{repo.name}' rejected (first claimed by '{first_repo}')",
                    file=sys.stderr,
                )
                continue  # skip normal validation; slug is already taken
            if skill_id:
                seen_ids[skill_id] = repo.name
            # ── end uniqueness block ────────────────────────────────────────

            # Code-skill: logic.py must exist
            extra_issue = None
            if skill.get("skill_type") == "code":
                py_entry = skill.get("python_entry") or "logic.py"
                py_path = path.rsplit("/", 1)[0] + "/" + py_entry
                if not repo.exists(py_path):
                    extra_issue = Issue("error", "python_entry",
                                        f"code skill must include {py_entry} at {py_path}")

            status, reason, issues = validate_skill(skill)
            if extra_issue is not None:
                issues.append(extra_issue)
                if status == "ready":
                    status = "stub" if skill.get("owner_team") else "broken"
                    reason = extra_issue.message

            skill["status"] = status
            skill["status_reason"] = reason
            result.catalog.append(skill)
            result.issues_by_skill[f"{repo.name}/{path}"] = issues

    return result


# ---------------------------------------------------------------------------
# Changelog — diff between two catalog builds (B2.4)
# ---------------------------------------------------------------------------

def _catalog_hash(catalog: list) -> str:
    """Stable SHA-256 hash of a catalog for cache-invalidation ETags."""
    serialised = json.dumps(
        sorted(catalog, key=lambda s: s.get("skill_id", "")),
        sort_keys=True, default=str,
    ).encode()
    return hashlib.sha256(serialised).hexdigest()[:16]


def compute_changelog(old_catalog: list, new_catalog: list) -> dict:
    """
    Compute a structured diff between two catalog snapshots.

    The orchestrator consumes catalog_changelog.json on startup or after a
    registry_dispatch refresh to selectively invalidate its in-memory cache
    rather than evicting everything on every rebuild.

    Returns a dict:
      generated_at     ISO-8601 timestamp of this build
      previous_hash    short hash of the prior catalog (ETag / cache-bust key)
      current_hash     short hash of the new catalog
      added            list of skill_ids new in this build
      removed          list of skill_ids that were present and are now gone
      changed          list of {skill_id, changes: {field: {from, to}}}
      unchanged_count  number of skills with no tracked-field changes
      summary          human-readable one-liner, e.g. "2 added, 1 changed"
    """
    old_map = {s["skill_id"]: s for s in old_catalog if s.get("skill_id")}
    new_map = {s["skill_id"]: s for s in new_catalog if s.get("skill_id")}

    added = sorted(sid for sid in new_map if sid not in old_map)
    removed = sorted(sid for sid in old_map if sid not in new_map)
    changed = []
    unchanged_count = 0

    for sid in sorted(new_map):
        if sid not in old_map:
            continue
        diffs: dict[str, dict] = {}
        for f in CHANGELOG_TRACKED_FIELDS:
            old_val = old_map[sid].get(f)
            new_val = new_map[sid].get(f)
            if old_val != new_val:
                diffs[f] = {"from": old_val, "to": new_val}
        if diffs:
            changed.append({"skill_id": sid, "changes": diffs})
        else:
            unchanged_count += 1

    parts = []
    if added:
        parts.append(f"{len(added)} added")
    if removed:
        parts.append(f"{len(removed)} removed")
    if changed:
        parts.append(f"{len(changed)} changed")
    if not parts:
        parts.append("no changes")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "previous_hash": _catalog_hash(old_catalog),
        "current_hash": _catalog_hash(new_catalog),
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged_count": unchanged_count,
        "summary": ", ".join(parts),
    }


# ---------------------------------------------------------------------------
# Build report (markdown)
# ---------------------------------------------------------------------------

def render_report(result: BuildResult) -> str:
    lines = ["# Catalog build report", ""]
    counts = {"ready": 0, "stub": 0, "broken": 0}
    for s in result.catalog:
        st = s.get("status", "broken")
        counts[st] = counts.get(st, 0) + 1
    lines.append(
        f"**Total skills:** {len(result.catalog)}  ·  "
        f"ready: {counts['ready']}, stub: {counts['stub']}, broken: {counts['broken']}"
    )
    lines.append("")

    # ── Duplicate rejections callout ─────────────────────────────────────
    if result.duplicate_rejections:
        lines += ["## ⚠ Duplicate skill_id rejections", ""]
        lines.append(
            "The following skills were **rejected** because their `skill_id` was already "
            "claimed by another repo. First-claimer wins; the rejected team must rename "
            "their skill or coordinate with the first claimant."
        )
        lines.append("")
        lines.append("| Rejected repo | `skill_id` | First claimed by |")
        lines.append("|---|---|---|")
        for rej in result.duplicate_rejections:
            lines.append(
                f"| `{rej['rejected_repo']}` | `{rej['skill_id']}` "
                f"| `{rej['first_claimed_by']}` |"
            )
        lines.append("")

    by_repo = {}
    for s in result.catalog:
        by_repo.setdefault(s.get("source_repo", "?"), []).append(s)
    if by_repo:
        lines += ["## By repo", "", "| Repo | Total | Ready | Stub | Broken |",
                  "|------|------:|------:|-----:|-------:|"]
        for repo_name in sorted(by_repo):
            ss = by_repo[repo_name]
            r = sum(1 for s in ss if s.get("status") == "ready")
            st = sum(1 for s in ss if s.get("status") == "stub")
            b = sum(1 for s in ss if s.get("status") == "broken")
            lines.append(f"| `{repo_name}` | {len(ss)} | {r} | {st} | {b} |")
        lines.append("")

    lines += ["## Issues", ""]
    any_issue = False
    for path, issues in sorted(result.issues_by_skill.items()):
        if not issues:
            continue
        any_issue = True
        lines.append(f"### `{path}`")
        for i in issues:
            mark = "ERROR" if i.severity == "error" else "warn"
            lines.append(f"- **{mark}** [`{i.field}`] {i.message}")
        lines.append("")
    if not any_issue:
        lines.append("_All skills passed validation cleanly._")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Catalog cleanup
# ---------------------------------------------------------------------------

INTERNAL_FIELDS = {"_parse_error"}

def clean_catalog(catalog: list) -> list:
    return [{k: v for k, v in s.items() if k not in INTERNAL_FIELDS} for s in catalog]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Build the Mentora skills catalog.")
    ap.add_argument("--local", help="Path to a local directory whose subdirs are team repos")
    ap.add_argument("--output", default="catalog.json", help="Catalog output path")
    ap.add_argument("--report", default="build_report.md", help="Build report output path")
    ap.add_argument(
        "--changelog", default="catalog_changelog.json",
        help="Changelog output path (diff between previous and new catalog)",
    )
    ap.add_argument(
        "--meta", default="catalog_meta.json",
        help="Catalog metadata output path (schema version, build timestamp, skill counts)",
    )
    ap.add_argument(
        "--strict", action="store_true",
        help=(
            "Exit with status 1 if any skill has status 'broken'. "
            "Enabled automatically on repository_dispatch triggers in CI. "
            "Use when a team push should be gated on a clean build."
        ),
    )
    args = ap.parse_args()

    if args.local:
        root = Path(args.local).resolve()
        if not root.is_dir():
            print(f"ERROR: {root} is not a directory", file=sys.stderr)
            return 2
        print(f"Scanning local dir: {root}")
        repos = discover_local_repos(root)
    else:
        org = os.environ.get("GITHUB_ORG")
        token = os.environ.get("GITHUB_TOKEN")
        if not (org and token):
            print("ERROR: set GITHUB_ORG and GITHUB_TOKEN, or use --local", file=sys.stderr)
            return 2
        print(f"Scanning GitHub org: {org}")
        repos = discover_github_repos(org, token)

    print(f"Found {len(repos)} team repo(s)")

    # ── Load previous catalog for changelog computation ────────────────────
    old_catalog: list = []
    output_path = Path(args.output)
    if output_path.exists():
        try:
            old_catalog = json.loads(output_path.read_text(encoding="utf-8"))
            print(f"Loaded previous catalog ({len(old_catalog)} entries) for changelog diff")
        except Exception as exc:
            print(f"Warning: could not load previous catalog for diff: {exc}", file=sys.stderr)

    # ── Build ──────────────────────────────────────────────────────────────
    result = build_catalog(repos)
    print(f"Built catalog with {len(result.catalog)} skills")

    cleaned = clean_catalog(result.catalog)

    # ── Write outputs ──────────────────────────────────────────────────────
    output_path.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")

    Path(args.report).write_text(render_report(result), encoding="utf-8")
    print(f"Wrote {args.report}")

    # ── Write catalog metadata (schema version + build info) ───────────────
    counts = {"ready": 0, "stub": 0, "broken": 0}
    for s in cleaned:
        counts[s.get("status", "broken")] = counts.get(s.get("status", "broken"), 0) + 1
    meta = {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog_hash": _catalog_hash(cleaned),
        "total_skills": len(cleaned),
        "by_status": counts,
    }
    Path(args.meta).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {args.meta}  (schema_version={CATALOG_SCHEMA_VERSION})")

    changelog = compute_changelog(old_catalog, cleaned)
    Path(args.changelog).write_text(json.dumps(changelog, indent=2), encoding="utf-8")
    print(f"Wrote {args.changelog}  ({changelog['summary']})")

    # ── Duplicate summary to stderr ────────────────────────────────────────
    if result.duplicate_rejections:
        print(
            f"\nERROR: {len(result.duplicate_rejections)} duplicate skill_id rejection(s):",
            file=sys.stderr,
        )
        for rej in result.duplicate_rejections:
            print(
                f"  skill_id='{rej['skill_id']}': "
                f"'{rej['rejected_repo']}' rejected "
                f"(first claimed by '{rej['first_claimed_by']}')",
                file=sys.stderr,
            )

    # ── B2.2: strict mode exit code ────────────────────────────────────────
    if args.strict:
        broken = [s for s in result.catalog if s.get("status") == "broken"]
        if broken:
            print(
                f"\nSTRICT MODE: {len(broken)} broken skill(s) found — exiting with status 1.",
                file=sys.stderr,
            )
            for s in broken:
                print(
                    f"  {s.get('source_repo', '?')}/{s.get('source_path', '?')}: "
                    f"{s.get('status_reason', 'validation failed')}",
                    file=sys.stderr,
                )
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

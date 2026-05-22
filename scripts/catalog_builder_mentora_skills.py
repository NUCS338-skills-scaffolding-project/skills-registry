#!/usr/bin/env python3
"""
catalog_builder_mentora_skills.py — Mentora package-mode catalog builder

Reads skills directly from the mentora_skills/skills/ package directory and
writes a slim catalog.json (selection-time fields only — the orchestrator loads
the full skills.md at runtime after skill selection).

Because skills in this package are not owned by separate teams, the build
report uses a flat issues table rather than per-team grouping.

Usage:
  python catalog_builder_mentora_skills.py
  python catalog_builder_mentora_skills.py --package ../mentora-skills/mentora_skills/skills
  python catalog_builder_mentora_skills.py --package . --output catalog.json --report build_report.md

For team-repo validation (GitHub org / local team dirs) use:
  catalog_builder_team_repo.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import yaml


# ---------------------------------------------------------------------------
# Tiny inline frontmatter parser
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

CATALOG_SCHEMA_VERSION = "1.0.0"

INSTRUCTIONAL_BODY_SECTIONS = {
    "description", "when_to_trigger", "tutor_stance", "flow",
    "safe_output_types", "must_avoid", "example_exchange",
}
CODE_BODY_SECTIONS = {
    "description", "when_to_trigger", "inputs", "outputs", "usage", "notes",
}

CHANGELOG_TRACKED_FIELDS = [
    "status", "version", "name", "skill_type", "stance",
    "owner_team", "owner_contact", "source_repo",
]

# Fields kept in the slim catalog
_SLIM_FIELDS = {
    "skill_id", "name", "version", "status",
    "skill_type", "stance",
    "tags", "course_types", "learning_goal_tags", "trigger_signals",
    "chip_icon", "has_logic", "owner_team",
}


# ---------------------------------------------------------------------------
# Repo handle — wraps a single skill directory as a virtual repo
# ---------------------------------------------------------------------------

@dataclass
class RepoHandle:
    name: str
    read: Callable[[str], Optional[str]]
    exists: Callable[[str], bool]
    list_files: Callable[[str], list]
    source_url_base: Optional[str] = None


def discover_from_package(skills_root: Path) -> list:
    """
    Discover skills from the mentora_skills/skills/ package directory.
    Each subdirectory with a skills.md is treated as one skill.
    """
    repos = []
    for skill_dir in sorted(d for d in skills_root.iterdir() if d.is_dir()):
        if not (skill_dir / "skills.md").exists():
            continue
        repos.append(_package_skill_handle(skill_dir))
    return repos


def _package_skill_handle(skill_dir: Path) -> RepoHandle:
    def read(rel: str) -> str | None:
        filename = rel.split("/")[-1]
        p = skill_dir / filename
        return p.read_text(encoding="utf-8") if p.is_file() else None

    def exists(rel: str) -> bool:
        filename = rel.split("/")[-1]
        return (skill_dir / filename).exists()

    def list_files(prefix: str) -> list:
        if (skill_dir / "skills.md").exists():
            return [f"{prefix.rstrip('/')}/skills.md"]
        return []

    return RepoHandle(name=skill_dir.name, read=read, exists=exists, list_files=list_files)


# ---------------------------------------------------------------------------
# Body parsing
# ---------------------------------------------------------------------------

def _normalize_heading(h: str) -> str:
    h = h.strip().lower()
    h = re.sub(r"[^a-z0-9]+", "_", h)
    return h.strip("_")

def parse_body_sections(body: str) -> dict:
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
# Skill loading
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
    return skill


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    severity: str   # "error" | "warning"
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
# Build pass
# ---------------------------------------------------------------------------

@dataclass
class BuildResult:
    catalog: list = field(default_factory=list)
    issues_by_skill: dict = field(default_factory=dict)
    duplicate_rejections: list = field(default_factory=list)


def build_catalog(repos: list) -> BuildResult:
    result = BuildResult()
    seen_ids: dict[str, str] = {}

    for repo in repos:
        skills_paths = [p for p in repo.list_files("skills") if p.endswith("/skills.md")]
        if not skills_paths:
            continue

        for path in skills_paths:
            print(f"  scanning {repo.name}/{path}", file=sys.stderr)
            skill = load_skill_from_path(repo, path)
            if skill is None:
                continue

            # owner_team defaults to skill dir name in package mode
            skill.setdefault("owner_team", repo.name)
            skill.setdefault("owner_contact", None)

            skill_id = skill.get("skill_id", "")
            if skill_id and skill_id in seen_ids:
                first_repo = seen_ids[skill_id]
                dup_msg = (
                    f"skill_id '{skill_id}' is already claimed by '{first_repo}'. "
                    f"Skill '{repo.name}' is rejected. Rename to avoid the conflict."
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
                print(f"  ERROR: duplicate skill_id '{skill_id}' — '{repo.name}' rejected",
                      file=sys.stderr)
                continue
            if skill_id:
                seen_ids[skill_id] = repo.name

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
# Changelog
# ---------------------------------------------------------------------------

def _catalog_hash(catalog: list) -> str:
    serialised = json.dumps(
        sorted(catalog, key=lambda s: s.get("skill_id", "")),
        sort_keys=True, default=str,
    ).encode()
    return hashlib.sha256(serialised).hexdigest()[:16]


def compute_changelog(old_catalog: list, new_catalog: list) -> dict:
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
# Catalog cleanup
# ---------------------------------------------------------------------------

INTERNAL_FIELDS = {"_parse_error"}

def clean_catalog(catalog: list) -> list:
    return [{k: v for k, v in s.items() if k not in INTERNAL_FIELDS} for s in catalog]

def slim_catalog(catalog: list) -> list:
    """Strip body content — keep only selection-time fields."""
    result = []
    for entry in catalog:
        slim = {k: v for k, v in entry.items() if k in _SLIM_FIELDS}
        slim.setdefault("has_logic", entry.get("skill_type") == "code"
                        and entry.get("status") != "broken")
        result.append(slim)
    return result


# ---------------------------------------------------------------------------
# Build report — flat layout (no team grouping)
# ---------------------------------------------------------------------------

def render_report(result: BuildResult) -> str:
    lines = ["# Catalog build report (mentora-skills package)", ""]

    counts = {"ready": 0, "stub": 0, "broken": 0}
    for s in result.catalog:
        st = s.get("status", "broken")
        counts[st] = counts.get(st, 0) + 1

    # Summary table
    lines += [
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Total skills | {len(result.catalog)} |",
        f"| Ready | {counts['ready']} |",
        f"| Stub | {counts['stub']} |",
        f"| Broken | {counts['broken']} |",
        "",
    ]

    # Duplicate rejections
    if result.duplicate_rejections:
        lines += ["## ⚠ Duplicate skill_id rejections", ""]
        lines += [
            "| Rejected skill | `skill_id` | First claimed by |",
            "|---|---|---|",
        ]
        for rej in result.duplicate_rejections:
            lines.append(
                f"| `{rej['rejected_repo']}` | `{rej['skill_id']}` "
                f"| `{rej['first_claimed_by']}` |"
            )
        lines.append("")

    # Skills with issues (stub / broken only)
    non_ready = [s for s in result.catalog if s.get("status") in ("stub", "broken")]
    lines += ["## Skills needing attention", ""]
    if non_ready:
        lines += [
            "| Skill | Status | Error |",
            "|-------|--------|-------|",
        ]
        for s in sorted(non_ready, key=lambda x: x.get("source_repo", "")):
            skill_name = s.get("source_repo", "?")
            status = s.get("status", "?")
            reason = s.get("status_reason") or ""
            lines.append(f"| `{skill_name}` | {status} | {reason} |")
    else:
        lines.append("_All skills are ready._")
    lines.append("")

    # Flat issues table
    lines += ["## Issues", ""]
    all_issues = [
        (path, i)
        for path, issues in sorted(result.issues_by_skill.items())
        for i in issues
    ]
    if all_issues:
        lines += [
            "| Skill | Severity | Field | Message |",
            "|-------|----------|-------|---------|",
        ]
        for path, i in all_issues:
            skill_name = path.split("/")[0]
            severity = "ERROR" if i.severity == "error" else "warn"
            lines.append(f"| `{skill_name}` | **{severity}** | `{i.field}` | {i.message} |")
    else:
        lines.append("_All skills passed validation cleanly._")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build the Mentora skills catalog from the mentora_skills package."
    )
    ap.add_argument(
        "--package",
        help=(
            "Path to mentora_skills/skills/ package directory. "
            "Defaults to ../mentora-skills/mentora_skills/skills relative to this script."
        ),
    )
    ap.add_argument("--output", default="catalog.json", help="Catalog output path")
    ap.add_argument("--report", default="build_report.md", help="Build report output path")
    ap.add_argument("--changelog", default="catalog_changelog.json", help="Changelog output path")
    ap.add_argument("--meta", default="catalog_meta.json", help="Catalog metadata output path")
    ap.add_argument(
        "--strict", action="store_true",
        help="Exit with status 1 if any skill is broken.",
    )
    args = ap.parse_args()

    pkg_path = args.package or str(
        Path(__file__).parent.parent.parent / "mentora-skills" / "mentora_skills" / "skills"
    )
    skills_root = Path(pkg_path).resolve()
    if not skills_root.is_dir():
        print(f"ERROR: {skills_root} is not a directory", file=sys.stderr)
        print("Pass an explicit --package path or ensure mentora-skills is a sibling directory.",
              file=sys.stderr)
        return 2

    print(f"Package mode — reading from: {skills_root}")
    repos = discover_from_package(skills_root)
    print(f"Found {len(repos)} skill(s)")

    old_catalog: list = []
    output_path = Path(args.output)
    if output_path.exists():
        try:
            old_catalog = json.loads(output_path.read_text(encoding="utf-8"))
            print(f"Loaded previous catalog ({len(old_catalog)} entries) for changelog diff")
        except Exception as exc:
            print(f"Warning: could not load previous catalog for diff: {exc}", file=sys.stderr)

    result = build_catalog(repos)
    print(f"Built catalog with {len(result.catalog)} skills")

    cleaned = clean_catalog(result.catalog)
    catalog_to_write = slim_catalog(cleaned)

    output_path.write_text(json.dumps(catalog_to_write, indent=2), encoding="utf-8")
    print(f"Wrote {args.output} (slim — body content excluded)")

    Path(args.report).write_text(render_report(result), encoding="utf-8")
    print(f"Wrote {args.report}")

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

    if result.duplicate_rejections:
        print(f"\nERROR: {len(result.duplicate_rejections)} duplicate skill_id rejection(s):",
              file=sys.stderr)
        for rej in result.duplicate_rejections:
            print(f"  skill_id='{rej['skill_id']}': '{rej['rejected_repo']}' rejected "
                  f"(first claimed by '{rej['first_claimed_by']}')", file=sys.stderr)

    if args.strict:
        broken = [s for s in result.catalog if s.get("status") == "broken"]
        if broken:
            print(f"\nSTRICT MODE: {len(broken)} broken skill(s) — exiting with status 1.",
                  file=sys.stderr)
            for s in broken:
                print(f"  {s.get('source_repo', '?')}: {s.get('status_reason', 'validation failed')}",
                      file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

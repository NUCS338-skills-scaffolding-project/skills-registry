# skills-registry

Central registry and aggregated catalog for every skill across the CS-338 teams.

## What's in here

| File | Description |
|---|---|
| `catalog.json` | Auto-generated index of every skill across all team repos. Rebuilt on push (webhook) and daily at midnight. |
| `catalog_changelog.json` | Diff between the previous and current catalog — added, removed, changed skills. Consumed by the orchestrator for selective cache invalidation. |
| `build_report.md` | Human-readable build summary. Lists each skill's status and any validation issues. Read this if your skill isn't appearing correctly. |
| `scripts/catalog_builder.py` | Walks team repos, parses each `skills.md`, validates against the v1 contract, writes the catalog + report + changelog. |
| `scripts/fetch_skills.py` | CLI to fetch a single skill by id into your working directory. |
| `vocab/learning_goals.yaml` | Controlled vocabulary for `learning_goal_tags`. Propose new tags via PR. |

---

## How the catalog is rebuilt

### Triggers

The catalog rebuilds automatically in three situations:

1. **Team repo push (webhook)** — When any team repo pushes a change to `skills/**` or `metadata.yaml`, a GitHub Actions workflow in the team repo (`notify-registry.yml`) fires a `repository_dispatch` event to this repo. The catalog rebuilds within ~1 minute and runs in **strict mode** (broken skills fail the build).

2. **Nightly schedule** — The catalog rebuilds every day at midnight UTC. This is a safety-net catch-all for repos that don't have the notify workflow set up yet. Strict mode is off on scheduled runs.

3. **Manual** — Trigger via the Actions tab → "Build Skills Catalog" → "Run workflow". Optionally enable strict mode.

### Setting up webhook re-crawl in your team repo

Add `REGISTRY_DISPATCH_TOKEN` as a secret in your team repo (Settings → Secrets → Actions → New secret). Ask the Admin for the token value — it is a fine-grained PAT scoped to the `skills-registry` repo with `Contents: Read & Write` permission.

Once the secret is in place, the `notify-registry.yml` workflow shipped with the `skill-standard-template` will automatically notify the registry whenever you push to `skills/**`.

If the secret is not set, the notification step is skipped gracefully and your changes will be picked up by the nightly build instead.

---

## Validation and strict mode

Every skill is validated against the v1 contract when the catalog is built. Skills land with one of three statuses:

| Status | Meaning | Orchestrator behaviour |
|---|---|---|
| `ready` | Passed all required checks | Can be invoked |
| `stub` | Has an owner team but is missing required fields | Shown as a disabled chip with the team name |
| `broken` | Failed validation with no clear owner, or is a duplicate | Ignored by the orchestrator |

### Strict mode (`--strict`)

When the catalog builder runs with `--strict`, it exits with status 1 if any skill has status `broken`. This is enabled automatically on webhook-triggered (repository_dispatch) builds — meaning a team push that introduces a broken skill will fail the CI run and surface the error immediately.

To test locally:

```bash
python scripts/catalog_builder.py --local /path/to/parent --strict
```

The build report and changelog are still written even when strict mode fails, so you can inspect the errors.

---

## skill_id uniqueness enforcement

`skill_id` values are globally unique across the registry. If two repos define the same `skill_id`, **the first repo to be scanned wins** and the second is rejected with a clear error.

The rejection is surfaced in three places:

1. **stderr** during the build run
2. **build_report.md** — a "Duplicate skill_id rejections" table at the top
3. **The rejected skill** — added to the catalog as `status: broken` with the reason

**If your skill is rejected as a duplicate:**
- Check `build_report.md` to see which repo claimed the slug first
- Either rename your `skill_id` (and matching folder name), or coordinate with the other team to transfer ownership

The alphabetical scan order of repos is stable but arbitrary — if there is a genuine ownership dispute, contact the Admin to reserve a slug via the SKIP_REPOS list.

---

## Changelog (`catalog_changelog.json`)

After every build, `catalog_changelog.json` is written alongside `catalog.json`. It contains a structured diff of what changed between the previous and current catalog:

```json
{
  "generated_at": "2026-05-01T12:00:00Z",
  "previous_hash": "4f53cda18c2baa0c",
  "current_hash": "b6bee2f0a00b208b",
  "added":   ["new-skill-id"],
  "removed": ["old-skill-id"],
  "changed": [
    {
      "skill_id": "counter-example",
      "changes": {
        "status": {"from": "stub", "to": "ready"},
        "version": {"from": "0.1.0", "to": "0.2.0"}
      }
    }
  ],
  "unchanged_count": 12,
  "summary": "1 added, 1 changed"
}
```

The `previous_hash` / `current_hash` fields are short SHA-256 hashes of the full catalog — suitable for use as HTTP ETags or cache-bust keys. The orchestrator uses these to decide whether to invalidate its in-memory skill cache after a registry refresh, avoiding a full eviction when only one skill changed.

---

## Storage backend

The registry uses **flat JSON** (`catalog.json`) as its storage format. This is intentional for the current scale (tens of skills across tens of team repos):

- **No infrastructure required** — the catalog is a committed file, readable by any tool
- **Git-native diffing** — `git diff catalog.json` shows exactly what changed between builds
- **Simple orchestrator integration** — the orchestrator fetches a single URL and parses JSON
- **Changelog replaces query complexity** — `catalog_changelog.json` gives the orchestrator the diff it needs without SQL

**Migration path if scale demands it:** If the catalog grows beyond ~500 skills or the orchestrator needs rich queries (filter by `learning_goal_tags`, fuzzy search on `name`), the natural next step is SQLite — same file-based simplicity, adds indexing and querying without loading the full catalog into memory. `catalog_builder.py` would need a `--backend sqlite` flag and a one-time migration from `catalog.json`. Postgres would only be warranted if the registry becomes a multi-writer service with concurrent builds.

---

## Testing your skills locally (without pushing to git)

You can add your skills to the local catalog and test them in the orchestrator without committing or pushing anything. This is the recommended workflow while actively developing a skill.

### Folder layout

Clone all repos into the same parent folder — the catalog builder treats each subfolder as a team repo:

```
mentora/                        ← parent folder (name doesn't matter)
├── skills-registry/            ← this repo
├── skills-orchestrator/
├── skills-ui/
└── your-team-repo/             ← your skills live here
    ├── metadata.yaml
    └── skills/
        └── your-skill/
            └── skills.md
```

### Rebuild the catalog

From inside the `skills-registry` folder, run:

```bash
python scripts/catalog_builder.py --local ..
```

`..` points at the parent folder — the builder scans every sibling repo, finds your `skills/*/skills.md` files, validates them, and writes the updated `catalog.json` here.

Check `build_report.md` immediately after to see your skill's status and any validation errors:

```bash
cat build_report.md
```

### Tell the orchestrator to reload

The orchestrator caches the catalog in memory. After rebuilding, trigger a reload without restarting:

```bash
curl -X POST http://localhost:8080/registry/refresh \
  -H "Authorization: Bearer changeme-dev-token"
```

Your updated skills are now live. Open the UI and test.

### Iteration loop

```
edit skills.md  →  python scripts/catalog_builder.py --local ..  →  curl .../registry/refresh  →  test in UI
```

No push required at any step. Push to git when the skill is ready and you want it in the shared catalog.

---

## Building the catalog locally

```bash
pip install pyyaml requests

# Basic build against a local parent directory
python scripts/catalog_builder.py --local /path/to/parent/dir

# With all outputs named explicitly
python scripts/catalog_builder.py \
  --local /path/to/parent/dir \
  --output catalog.json \
  --report build_report.md \
  --changelog catalog_changelog.json

# Strict mode — exits 1 if any skill is broken
python scripts/catalog_builder.py --local /path/to/parent/dir --strict
```

The "parent directory" is the folder whose subdirectories are team repos. Repos named `skills-registry` and `skill-standard-template` are skipped automatically.

---

## Fetching a skill

```bash
python scripts/fetch_skills.py --id counter-example
```

---

## Catalog entry schema

Every entry in `catalog.json` follows the v0.1 contract. Key fields:

```json
{
  "skill_id": "counter-example",
  "name": "Counter-Example",
  "skill_type": "instructional",
  "stance": "socratic",
  "tags": ["essay", "argument", "kant"],
  "course_types": ["humanities"],
  "learning_goal_tags": ["construct-arguments", "engage-objections"],
  "description": "Pressure-tests the student's claim with a structured counter-example.",
  "trigger_summary": "Use when a student is defending a first position without engaging counter-evidence.",
  "tutor_stance_rules": ["..."],
  "flow": [{"step": 1, "title": "Surface the claim", "description": "..."}],
  "safe_outputs": ["..."],
  "must_avoid": ["..."],
  "owner_team": "PHIL-270",
  "owner_contact": "advisor@phil.edu",
  "status": "ready",
  "source_repo": "phil-270-skills",
  "source_path": "skills/counter-example/skills.md",
  "source_url": "https://github.com/.../skills/counter-example/skills.md"
}
```

If your skill is `stub`, open `build_report.md` for the specific fields to fix.

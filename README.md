# skills-registry

Central registry and aggregated catalog for every skill in the Mentora skills package.

## What's in here

| File | Description |
|---|---|
| `catalog.json` | Auto-generated index of every skill. Rebuilt on push (webhook) and daily at midnight. |
| `catalog_team.json` | Catalog built from team repos (used by the team-repo validation workflow). |
| `catalog_changelog.json` | Diff between the previous and current catalog — added, removed, changed skills. Consumed by the orchestrator for selective cache invalidation. |
| `catalog_meta.json` | Schema version, build timestamp, total skill count, and a hash of the catalog. |
| `local/` | Local build outputs — gitignored. Put any locally generated catalogs and reports here. |
| `scripts/catalog_builder_mentora_skills.py` | Builds the runtime `catalog.json` used by the orchestrator from the `mentora_skills` package. No GitHub token needed. This is the script teams use for local development. |
| `scripts/catalog_builder_team_repo.py` | **Admin only.** Validates skills directly in each team's GitHub repo and produces a per-team error report (`scripts/team_build_report.md`). This exists because the `mentora_skills` package flattens ownership — once a skill is merged in, there's no way to trace which team introduced a broken skill. This script goes back to the source repos to answer that question and hold the right team accountable. Requires `GITHUB_TOKEN` and `GITHUB_ORG`. Teams do not need to run this. |
| `vocab/learning_goals.yaml` | Controlled vocabulary for `learning_goal_tags`. Propose new tags via PR. |

---

## Building the catalog locally

No tokens or GitHub access needed — just point the builder at your local `mentora-skills` package.

### Prerequisites

```bash
pip install pyyaml
```

### Run the build

From inside the `skills-registry` folder:

```bash
python scripts/catalog_builder_mentora_skills.py \
  --package ../mentora-skills/mentora_skills/skills \
  --output local/catalog.json \
  --report local/build_report.md \
  --changelog local/catalog_changelog.json \
  --meta local/catalog_meta.json
```

If `mentora-skills` is already a sibling of `skills-registry`, the `--package` flag can be omitted — the builder defaults to `../mentora-skills/mentora_skills/skills`:

```bash
python scripts/catalog_builder_mentora_skills.py \
  --output local/catalog.json \
  --report local/build_report.md \
  --changelog local/catalog_changelog.json \
  --meta local/catalog_meta.json
```

Check the report immediately after to see each skill's status and any validation errors:

```bash
cat local/build_report.md
```

### Strict mode

Add `--strict` to exit with status 1 if any skill is `broken` — useful for catching errors before pushing:

```bash
python scripts/catalog_builder_mentora_skills.py --strict \
  --output local/catalog.json \
  --report local/build_report.md \
  --changelog local/catalog_changelog.json \
  --meta local/catalog_meta.json
```

---

## Iteration loop for skill development

```
edit skills.md  →  python scripts/catalog_builder_mentora_skills.py [flags]  →  restart orchestrator  →  test in UI
```

No push required at any step. Push to git when the skill is ready.

---

## How the catalog is rebuilt in CI

The catalog on GitHub is always up to date — just pull `catalog.json` to get the latest. Teams don't need to trigger or configure anything.

The rebuild runs automatically in two situations:

1. **Nightly schedule** — Rebuilds every day at midnight UTC. Strict mode is off.
2. **Manual** — Trigger via Actions → "Build Skills Catalog" → "Run workflow". Optionally enable strict mode.

---

## Validation

Every skill is validated against the v1 contract when the catalog is built. Skills land with one of three statuses:

| Status | Meaning | Orchestrator behaviour |
|---|---|---|
| `ready` | Passed all required checks | Can be invoked |
| `stub` | Has an owner team but is missing required fields | Shown as a disabled chip with the team name |
| `broken` | Failed validation with no clear owner, or is a duplicate | Ignored by the orchestrator |

If your skill is `stub` or `broken`, check `local/build_report.md` for the specific fields to fix.

---

## skill_id uniqueness

`skill_id` values are globally unique across the registry. If two skills define the same `skill_id`, the first one scanned wins and the second is rejected with `status: broken`.

The rejection is surfaced in:
1. **stderr** during the build run
2. **build_report.md** — a "Duplicate skill_id rejections" table at the top
3. **The rejected skill entry** in the catalog with `status: broken`

If your skill is rejected as a duplicate, rename your `skill_id` (and matching folder name), or coordinate with the other owner.

---

## Changelog (`catalog_changelog.json`)

After every build, `catalog_changelog.json` is written alongside `catalog.json`. It contains a structured diff of what changed:

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

The `previous_hash` / `current_hash` fields are short SHA-256 hashes of the full catalog, used by the orchestrator to decide whether to invalidate its in-memory skill cache after a refresh.

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
  "trigger_signals": ["student is defending a first position"],
  "chip_icon": "⚡",
  "has_logic": false,
  "owner_team": "PHIL-270",
  "status": "ready",
  "version": "0.1.0"
}
```

Note: the slim catalog stored here contains only selection-time fields. The full `skills.md` body (flow, must_avoid, example_exchange, etc.) is loaded by the orchestrator at runtime after skill selection.

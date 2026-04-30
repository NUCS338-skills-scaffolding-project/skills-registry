# skills-registry

Central registry and aggregated catalog for every skill across the CS-338 teams.

## What's in here

- `catalog.json` — Auto-generated index of every skill across all team repos. Built daily on a cron and on every push to `scripts/`.
- `build_report.md` — Auto-generated alongside the catalog. Lists each skill's `ready` / `stub` / `broken` status and any validation issues. Read this if your skill isn't behaving as expected.
- `scripts/catalog_builder.py` — Walks team repos, parses each `skills.md`, validates against the v0.1 contract, writes the catalog + report.
- `scripts/fetch_skills.py` — CLI to fetch a single skill by id into your working directory.
- `vocab/learning_goals.yaml` — Controlled vocabulary for the `learning_goal_tags` field. Propose new tags via PR.

## Fetching a skill

```bash
python scripts/fetch_skills.py --id counter-example
```

## Building the catalog locally (for testing)

```bash
python scripts/catalog_builder.py --local /path/to/parent/dir
```

Walks the parent directory as if its subdirectories were team repos. Useful for previewing how the validator will react to a change before pushing.

## Authoring a new skill

If you're a team building skills, see **`Team-Guide.md`** in the `skill-standard-template` repo. That guide is the source-of-truth for the YAML schema, naming conventions, the four tutor stances, and what makes a skill `ready` vs `stub`.

## Catalog entry schema

Every entry in `catalog.json` follows the v0.1 contract: frontmatter fields, parsed body sections, owner enrichment, and validation status. A minimal example:

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

## Skill statuses

Every skill in the catalog is tagged with one of three statuses:

- **`ready`** — passed all validation. The orchestrator can invoke it.
- **`stub`** — has an owning team but is missing required fields or content. Visible in the catalog as a placeholder; the orchestrator surfaces it as a disabled chip with the team name.
- **`broken`** — failed validation with no clear owner. The orchestrator ignores these.

If your skill is `stub`, open `build_report.md` for the specific gaps to fill.
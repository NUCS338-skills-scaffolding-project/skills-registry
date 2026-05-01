# Catalog Schema Compatibility Policy

This document defines the versioning policy for the `catalog.json` schema produced by `scripts/catalog_builder.py` and consumed by the Mentora orchestrator's `registry_client.py`.

**Current schema version:** `1.0.0`

---

## Version constants

| Location | Constant | Value |
|---|---|---|
| `skills-registry/scripts/catalog_builder.py` | `CATALOG_SCHEMA_VERSION` | `"1.0.0"` |
| `orchestrator/app/services/registry_client.py` | `EXPECTED_CATALOG_SCHEMA_VERSION` | `"1.0.0"` |

These two constants must match at every deployment. If they diverge, the orchestrator logs an error or warning (see "Version mismatch behaviour" below).

The schema version is emitted in `catalog_meta.json` alongside `catalog.json` on every build:

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-05-01T12:00:00Z",
  "catalog_hash": "b6bee2f0a00b208b",
  "total_skills": 42,
  "by_status": {"ready": 38, "stub": 3, "broken": 1}
}
```

---

## Versioning rules (semantic)

The schema version follows semver (`MAJOR.MINOR.PATCH`). The orchestrator checks the **major** version for compatibility.

### Patch bump (`1.0.0` → `1.0.1`)

New **optional** output fields are added to `catalog.json` entries. Existing fields are unchanged. No consumer code needs to change.

**Examples:**
- Adding `chip_icon` to the output (was previously omitted even when set in skills.md)
- Adding a `last_modified_at` timestamp field

**Action required:** Update `CATALOG_SCHEMA_VERSION` in `catalog_builder.py`. Update `EXPECTED_CATALOG_SCHEMA_VERSION` in `registry_client.py`. No logic changes.

### Minor bump (`1.0.0` → `1.1.0`)

Existing fields are **renamed or restructured**, but the old field name is kept as a deprecated alias for exactly **one release cycle** (one semester) before being removed. New required fields may be added, but with backwards-compatible defaults.

**Examples:**
- Renaming `owner_team` → `team_id` (old `owner_team` kept in output for one cycle)
- Adding `required_learning_goals` with a default of `[]`

**Action required:**
1. Update `CATALOG_SCHEMA_VERSION` with a minor bump
2. Add the renamed/new field to `catalog_builder.py` output
3. Keep the deprecated field for backward compatibility in the same release
4. Update `registry_client._parse_catalog_entry()` to prefer the new field, fall back to old
5. Update `EXPECTED_CATALOG_SCHEMA_VERSION` in `registry_client.py`
6. Announce in `build_report.md` header and the team channel that the old field is deprecated
7. Remove the deprecated field in the **next** minor bump

### Major bump (`1.0.0` → `2.0.0`)

A **breaking change** that existing orchestrators cannot consume without code changes. This is rare and always requires a coordinated deployment.

**Examples:**
- Restructuring the catalog from a flat list to a versioned object `{"version": "2.0.0", "skills": [...]}`
- Removing a field that the orchestrator requires (e.g., removing `flow`)
- Changing the type of an existing field (e.g., `tags` from list to dict)

**Deployment procedure:**
1. Bump `CATALOG_SCHEMA_VERSION` in `catalog_builder.py`
2. Update `registry_client._parse_catalog_entry()` for the new schema
3. Update `EXPECTED_CATALOG_SCHEMA_VERSION` in `registry_client.py`
4. **Deploy the new orchestrator first**, then deploy the new registry
5. If rollback is needed, both services must roll back together

---

## Version mismatch behaviour (at runtime)

The orchestrator fetches `catalog_meta.json` on every registry refresh and compares schema versions:

| Situation | Log level | Action |
|---|---|---|
| Versions match | — | Silent |
| Same major, different minor/patch | `WARNING` | Continue; check SCHEMA_COMPAT.md |
| Different major | `ERROR` | Continue loading (no crash), but treat as a deployment blocker |
| `catalog_meta.json` absent | `DEBUG` | Silent; assume schema is compatible (older registry) |

A major-version mismatch will not crash the orchestrator (to avoid a production outage if the registry is deployed first). But the error log should be treated as a P1 alert and resolved within one working day.

---

## Adding a new field to `skills.md` (team-side)

Adding a new **optional** frontmatter field in `skills.md` (e.g., a new `difficulty` tag) is a **patch-level** change:
1. Teams can add it immediately — the builder passes through unknown fields in `extra_sections`
2. Open a PR to `vocab/learning_goals.yaml` if the field maps to the learning goal vocabulary
3. Propose the field for formal inclusion via a PR to `Team-Guide.md`
4. The field becomes a first-class schema field in the next catalog release

Adding a new **required** frontmatter field is a **minor-level** change and goes through the minor-bump process above.

---

## Backwards-compat test checklist

Before any version bump, verify:

- [ ] The existing golden catalog fixture (`orchestrator/tests/fixtures/golden_catalog.json`) still parses without errors through `_parse_catalog_entry()`
- [ ] `test_catalog_contract.py` passes with the new schema
- [ ] If fields were removed or renamed, `test_parser_robustness.py::test_missing_optional_fields_get_defaults` still passes
- [ ] The `catalog_meta.json` emitted by the new builder has the updated `schema_version`
- [ ] `EXPECTED_CATALOG_SCHEMA_VERSION` in `registry_client.py` matches the new version
- [ ] The build report and changelog are both written correctly after the change

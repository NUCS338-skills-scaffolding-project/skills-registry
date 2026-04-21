# skills-registry
Central registry and catalog for all skill repositories across CS-338

# What's in here?
- 'catalog.json' - Auto generated index of every skill across all team repos
- 'scripts/catalog_builder.py' - Script that builds the catalog
- 'scripts/fetch_skills.py'

## How to use
''' bash
python scripts/fetch_skills.py --id YOUR-SKILL-ID
  
## Catalog structure
Each entry in `catalog.json` follows this schema:
```json
  {
      "skill_id": "SKILL-NAME",
      "name": "Human Readable Name",
      "tags": ["topic1", "topic2"],
      "python_entry": "logic.py",
      "source_path": "path/to/skills.md"
  }

# fetch_skill.py
# CLI tool for teams to fetch a skill by its ID
# Usage: python fetch_skill.py --id sorting

import argparse
import json
import os
import shutil

def fetch_skill(skill_id):
  """
  Looks up a skill by ID in catalog.json
  and copies it into the current working directory
  """
  # Load the catalog
  with open("catalog.json") as f:
    catalog = json.load(f)

  # Search for the skill
    match = next((s for s in catalog if s.get("skill_id") == skill_id), None)

    if not match:
      print(f"ERROR:Skill '{skill_id}' not found in catalog.")
      return
    
    source = match.get("source_path")
    dest = os.path.join("./fetched-skills", skill_id)

    if not os.path.exists(source):
      print(f"ERROR:Source path not found: {source}")
      return

    shutil.copytree(os.path.dirname(source), dest, dirs_exist_ok=True)
    print(f"SUCCESS: Skill '{skill_id}' fetched to {dest}")

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--id", required=True, help="Skill ID to fetch")
  args = parser.parse_args()
  fetch_skill(args.id)

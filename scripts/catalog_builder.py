# catalog_builder.py
# Crawls all team repos and extracts skill metadata into catalog.json

import frontmatter
import json
import os

def build_registry(root_dir):
  """
  Scans all team skill directories for skills.md files
  and compiles their YAML metadata into a single catalog.json
  """
  registry = []
  for root, dirs, files in os.walk(root_dir):
    if "skills.md" in files:
      filepath = os.path.join(root, "skills.md")
      with open(filepath) as f:
        post = frontmatter.load(f)
        # Add the file path so we know where the skill lives
        metadata = post.metadata
        metadata["source_path"] = filepath
        registry.append(metadata)
  # Write the compiled catalog
  with open("catalog.json", "w") as f:
    json.dump(registry, f, indent=4)
    
  print(f"Catalog built with {len(registry)} skills.")

if __name__ == "__main__":
  # Point this at your local clone of all team repos
  build_registry("./team-repos")

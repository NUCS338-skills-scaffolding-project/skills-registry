# catalog_builder.py
# Crawls all team repos in the GitHub Organization
# and extracts skill metadata into catalog.json

import os
import json
import base64
import requests
import frontmatter
import io

# Get credentials from environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_ORG = os.environ.get("GITHUB_ORG")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_org_repos():
    """Get all repositories in the Organization"""
    repos = []
    page = 1

    while True:
        url = f"https://api.github.com/orgs/{GITHUB_ORG}/repos"
        response = requests.get(url, headers=HEADERS, params={"page": page, "per_page": 100})
        data = response.json()

        if not data:
            break

        # Skip the registry and template repos themselves
        for repo in data:
            if repo["name"] not in ["skills-registry", "skill-standard-template"]:
                repos.append(repo["name"])

        page += 1

    return repos

def get_skills_from_repo(repo_name):
    """Find all skills.md files in a repo and extract their metadata"""
    skills = []
    url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo_name}/git/trees/main?recursive=1"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"WARNING: Could not access {repo_name} — skipping")
        return skills

    tree = response.json().get("tree", [])

    for item in tree:
        if item["path"].endswith("skills.md"):
            # Fetch the file content
            file_url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo_name}/contents/{item['path']}"
            file_response = requests.get(file_url, headers=HEADERS)

            if file_response.status_code == 200:
                content = base64.b64decode(file_response.json()["content"]).decode("utf-8")
                post = frontmatter.load(io.StringIO(content))
                metadata = post.metadata

                # Add source info
                metadata["source_repo"] = repo_name
                metadata["source_path"] = item["path"]
                metadata["source_url"] = f"https://github.com/{GITHUB_ORG}/{repo_name}/tree/main/{item['path']}"

                skills.append(metadata)
                print(f" SUCCESS: Found skill: {metadata.get('skill_id', 'unknown')} in {repo_name}")

    return skills

def build_registry():
    """Main function — crawls all repos and builds catalog.json"""
    print(f"🔍 Scanning Organization: {GITHUB_ORG}\n")

    repos = get_org_repos()
    print(f"FOUND {len(repos)} team repos\n")

    registry = []

    for repo in repos:
        print(f"Scanning {repo}...")
        skills = get_skills_from_repo(repo)
        registry.extend(skills)

    # Write the catalog
    with open("catalog.json", "w") as f:
        json.dump(registry, f, indent=4)

    print(f"\nSUCCESS: Catalog built with {len(registry)} skills total.")

if __name__ == "__main__":
    build_registry()

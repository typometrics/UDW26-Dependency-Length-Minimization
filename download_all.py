#!/usr/bin/env python3
"""
Download all UD 2.17 and SUD 2.17 treebanks.

UD: Full release from LINDAT (tgz archive)
SUD: Individual repos from GitHub (surfacesyntacticud org), using the GitHub API
"""
import os
import sys
import json
import subprocess
import tarfile
import urllib.request
import urllib.error
import time

# --- Configuration ---
BASE_DIR = "."
UD_DATA_DIR = os.path.join(BASE_DIR, "data_ud")
SUD_DATA_DIR = os.path.join(BASE_DIR, "data_sud")

# UD 2.17 release archive
UD_URL = "https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-6036/ud-treebanks-v2.17.tgz"
UD_ARCHIVE = os.path.join(BASE_DIR, "ud-treebanks-v2.17.tgz")

# SUD GitHub org
SUD_GITHUB_API = "https://api.github.com/orgs/surfacesyntacticud/repos"

def download_ud():
    """Download and extract the full UD 2.17 release."""
    os.makedirs(UD_DATA_DIR, exist_ok=True)

    if os.path.exists(UD_ARCHIVE):
        print(f"UD archive already exists: {UD_ARCHIVE}")
    else:
        print(f"Downloading UD 2.17 from {UD_URL}...")
        print("(This is ~2GB, may take a few minutes)")
        try:
            urllib.request.urlretrieve(UD_URL, UD_ARCHIVE)
            print(f"Downloaded to {UD_ARCHIVE}")
        except Exception as e:
            print(f"urllib failed: {e}")
            print("Trying curl...")
            subprocess.run(["curl", "-L", "-o", UD_ARCHIVE, UD_URL], check=True)

    # Extract .conllu files
    print(f"Extracting UD treebanks to {UD_DATA_DIR}...")
    count = 0
    with tarfile.open(UD_ARCHIVE, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith(".conllu") and not member.name.startswith("._"):
                # Extract treebank name from path: ud-treebanks-v2.17/UD_Language-Treebank/file.conllu
                parts = member.name.split("/")
                if len(parts) >= 3:
                    treebank_name = parts[1]  # e.g., UD_English-EWT
                    filename = parts[2]
                    # Create treebank directory
                    tb_dir = os.path.join(UD_DATA_DIR, treebank_name)
                    os.makedirs(tb_dir, exist_ok=True)
                    # Extract file
                    member.name = os.path.join(treebank_name, filename)
                    tar.extract(member, UD_DATA_DIR)
                    count += 1

    print(f"Extracted {count} .conllu files from UD 2.17")

def download_sud():
    """Download SUD treebanks from GitHub."""
    os.makedirs(SUD_DATA_DIR, exist_ok=True)

    # Get list of SUD repos from GitHub API
    print("Fetching SUD repository list from GitHub...")
    repos = []
    page = 1
    while True:
        url = f"{SUD_GITHUB_API}?per_page=100&page={page}"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "UDW-Research-Script")

        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read())
                if not data:
                    break
                repos.extend(data)
                page += 1
                time.sleep(0.5)  # Rate limiting
        except urllib.error.HTTPError as e:
            print(f"GitHub API error: {e}")
            break

    # Filter for SUD treebank repos (they start with SUD_)
    sud_repos = [r for r in repos if r["name"].startswith("SUD_")]
    print(f"Found {len(sud_repos)} SUD treebank repos")

    # Clone each repo (shallow clone)
    for i, repo in enumerate(sud_repos):
        repo_name = repo["name"]
        clone_url = repo["clone_url"]
        target_dir = os.path.join(SUD_DATA_DIR, repo_name)

        if os.path.exists(target_dir):
            print(f"  [{i+1}/{len(sud_repos)}] {repo_name} already exists, skipping")
            continue

        print(f"  [{i+1}/{len(sud_repos)}] Cloning {repo_name}...")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, target_dir],
                capture_output=True, text=True, timeout=60
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            print(f"    Failed to clone {repo_name}: {e}")
            continue
        time.sleep(0.3)  # Rate limiting

    print(f"SUD download complete")

def main():
    print("=" * 60)
    print("Downloading all UD 2.17 and SUD 2.17 treebanks")
    print("=" * 60)

    download_ud()
    print()
    download_sud()

    # Summary
    ud_treebanks = [d for d in os.listdir(UD_DATA_DIR) if d.startswith("UD_")]
    sud_treebanks = [d for d in os.listdir(SUD_DATA_DIR) if d.startswith("SUD_")]
    print(f"\n{'=' * 60}")
    print(f"Download complete:")
    print(f"  UD treebanks: {len(ud_treebanks)}")
    print(f"  SUD treebanks: {len(sud_treebanks)}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()

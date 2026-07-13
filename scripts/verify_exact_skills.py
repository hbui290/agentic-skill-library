import os
import json
import sys

from update_skills import find_leaf_skills

def main():
    skills_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(skills_dir, ".antigravity-install-manifest.json")
    
    if not os.path.exists(manifest_path):
        print(f"Error: Manifest file not found at {manifest_path}")
        return 1

    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    entries = data.get("entries", [])
    print(f"Manifest has {len(entries)} entries.")

    failed = False

    # Check for duplicates
    if len(entries) != len(set(entries)):
        failed = True
        print("ERROR: Duplicate entries found in manifest.")
        seen = set()
        dupes = []
        for x in entries:
            if x in seen:
                dupes.append(x)
            seen.add(x)
        print("Duplicates:", dupes)
    else:
        print("SUCCESS: No duplicate entries in manifest.")

    manifest_entries = set(entries)
    disk_entries = set(find_leaf_skills())
    missing = sorted(manifest_entries - disk_entries)
    extra = sorted(disk_entries - manifest_entries)

    if missing:
        failed = True
        print(f"ERROR: {len(missing)} manifest entries do not exist on disk!")
        print("Missing:", missing[:10])
    else:
        print("SUCCESS: Every manifest entry exists on disk!")

    if extra:
        failed = True
        print(f"ERROR: {len(extra)} skill directories on disk are absent from manifest!")
        print("Extra:", extra[:10])
    else:
        print("SUCCESS: No extra skill directories exist on disk!")

    without_marker = [entry for entry in sorted(disk_entries)
                      if not os.path.isfile(os.path.join(skills_dir, entry, "SKILL.md"))]
    if without_marker:
        print(f"WARN: {len(without_marker)} skill directories have no SKILL.md:",
              without_marker[:10])

    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())

import os
import json
import shutil

skills_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
flat_dir = os.path.abspath(os.path.join(skills_dir, "..", "flat-skills"))
manifest_path = os.path.join(skills_dir, ".antigravity-install-manifest.json")

def clean_dir(target_dir):
    if os.path.exists(target_dir):
        for name in os.listdir(target_dir):
            path = os.path.join(target_dir, name)
            try:
                if os.path.islink(path) or os.path.isfile(path):
                    os.unlink(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            except Exception as e:
                print(f"Error removing {path}: {e}")
    else:
        os.makedirs(target_dir, exist_ok=True)

def sync_skill(src_path, dest_skill_dir):
    os.makedirs(dest_skill_dir, exist_ok=True)
    # Symlink all contents of src_path into dest_skill_dir
    for item in os.listdir(src_path):
        src_item = os.path.join(src_path, item)
        dest_item = os.path.join(dest_skill_dir, item)
        if os.path.exists(dest_item) or os.path.islink(dest_item):
            try:
                if os.path.islink(dest_item) or os.path.isfile(dest_item):
                    os.unlink(dest_item)
                elif os.path.isdir(dest_item):
                    shutil.rmtree(dest_item)
            except Exception as e:
                print(f"Error cleaning {dest_item}: {e}")
                continue
        try:
            os.symlink(src_item, dest_item)
        except Exception as e:
            print(f"Error symlinking {src_item} -> {dest_item}: {e}")

def main():
    if not os.path.exists(manifest_path):
        print("Manifest file not found!")
        return
        
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    entries = data.get("entries", [])

    # Clean flat_dir
    clean_dir(flat_dir)

    # Shared flat-naming rule (same helper the librarian index uses)
    from update_skills import flat_name_map
    fmap = flat_name_map(entries)

    created_flat = 0
    duplicates_resolved = 0

    for entry in entries:
        src_path = os.path.join(skills_dir, entry)
        if not os.path.isdir(src_path):
            continue

        symlink_name = fmap[entry]
        if symlink_name != os.path.basename(entry):
            duplicates_resolved += 1

        # Sync to flat_dir
        dest_flat_dir = os.path.join(flat_dir, symlink_name)
        sync_skill(src_path, dest_flat_dir)
        created_flat += 1
            
    print(f"Flat directory: Synced {created_flat} skills.")
    print(f"Resolved {duplicates_resolved} duplicate names.")

if __name__ == "__main__":
    main()

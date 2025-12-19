"""Archive or remove TypeScript files since they're deprecated"""
import os
import shutil
from pathlib import Path

def archive_typescript():
    """Archive TypeScript files to archive/ folder"""
    project_root = Path(__file__).parent
    archive_dir = project_root / "archive"
    src_dir = project_root / "src"
    
    print("="*60)
    print("TypeScript Files Archive/Removal")
    print("="*60)
    print()
    
    if not src_dir.exists():
        print("✅ src/ directory doesn't exist - nothing to archive")
        return
    
    print("TypeScript files found in src/:")
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(('.ts', '.tsx', '.js', '.json')):
                rel_path = Path(root).relative_to(project_root) / file
                print(f"  - {rel_path}")
    print()
    
    choice = input("Archive (a) or Delete (d) TypeScript files? [a/d]: ").strip().lower()
    
    if choice == 'a':
        # Archive
        archive_dir.mkdir(exist_ok=True)
        archive_src = archive_dir / "src_typescript_reference"
        
        if archive_src.exists():
            print(f"⚠️  Archive already exists at {archive_src}")
            overwrite = input("Overwrite? [y/n]: ").strip().lower()
            if overwrite != 'y':
                print("Cancelled")
                return
            shutil.rmtree(archive_src)
        
        print(f"Archiving src/ to {archive_src}...")
        shutil.copytree(src_dir, archive_src)
        
        # Also archive package.json and tsconfig.json if they exist
        for file in ['package.json', 'tsconfig.json']:
            src_file = project_root / file
            if src_file.exists():
                archive_file = archive_dir / f"{file}.reference"
                print(f"Archiving {file} to {archive_file}...")
                shutil.copy2(src_file, archive_file)
        
        print()
        print("✅ TypeScript files archived!")
        print(f"   Location: {archive_src}")
        print()
        print("⚠️  src/ directory still exists. Delete it manually if desired:")
        print(f"   rmdir /s /q {src_dir}")
        
    elif choice == 'd':
        # Delete
        confirm = input("⚠️  Are you SURE you want to DELETE all TypeScript files? [yes/no]: ").strip().lower()
        if confirm == 'yes':
            print(f"Deleting {src_dir}...")
            shutil.rmtree(src_dir)
            print("✅ TypeScript files deleted!")
        else:
            print("Cancelled")
    else:
        print("Invalid choice. Cancelled.")

if __name__ == "__main__":
    archive_typescript()


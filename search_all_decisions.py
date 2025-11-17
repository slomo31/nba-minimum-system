"""
Search for ALL decision CSV files in project
"""
import os
import glob

print("=" * 80)
print("SEARCHING FOR ALL DECISION FILES")
print("=" * 80)
print()

# Search in multiple locations
search_paths = [
    'output_archive/decisions/*_decisions.csv',
    '*_decisions.csv',
    '**/*_decisions.csv'
]

all_files = set()

for pattern in search_paths:
    files = glob.glob(pattern, recursive=True)
    for f in files:
        all_files.add(os.path.abspath(f))

print(f"Found {len(all_files)} decision files:")
print("-" * 80)

for f in sorted(all_files):
    # Get file size and modification time
    stat = os.stat(f)
    size = stat.st_size
    import datetime
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
    
    print(f"  {f}")
    print(f"    Size: {size} bytes | Modified: {mtime.strftime('%Y-%m-%d %H:%M')}")
    
print()
print("=" * 80)
print("CHECKING WHICH FILES ARE BEING USED")
print("=" * 80)
print()

archive_files = glob.glob('output_archive/decisions/*_decisions.csv')
print(f"Files in output_archive/decisions/: {len(archive_files)}")

if len(all_files) > len(archive_files):
    print()
    print("⚠️  FOUND DECISION FILES OUTSIDE output_archive/decisions/")
    print("The tracker only reads from output_archive/decisions/")
    print()
    print("Files NOT being tracked:")
    print("-" * 80)
    archive_abs = set(os.path.abspath(f) for f in archive_files)
    for f in sorted(all_files):
        if f not in archive_abs:
            print(f"  {f}")

# scripts/update_last_modified.py

import subprocess
import os
import yaml

def get_last_modified_date(file):
    cmd = f"git log -1 --format=%cd -- {file}"
    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, text=True)
    return result.stdout.strip()

def update_last_modified(file):
    last_modified = get_last_modified_date(file)
    with open(file, 'r') as f:
        content = f.read()

    # Parse YAML front matter
    yaml_content = content.split('---', 2)
    if len(yaml_content) < 3:
        return

    metadata = yaml.safe_load(yaml_content[1])
    metadata['last_modified'] = last_modified

    # Reconstruct the file with updated metadata
    new_content = f"---\n{yaml.safe_dump(metadata)}---{yaml_content[2]}"
    with open(file, 'w') as f:
        f.write(new_content)

# Apply the function to all .qmd files
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.qmd'):
            update_last_modified(os.path.join(root, file))

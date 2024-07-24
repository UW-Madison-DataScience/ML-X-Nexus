import subprocess
import os
import yaml

def get_last_modified_date(file):
    cmd = f"git log -1 --format=%cd -- {file}"
    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, text=True)
    return result.stdout.strip()

def update_date_modified(file):
    last_modified = get_last_modified_date(file)
    with open(file, 'r') as f:
        content = f.read()

    # Parse YAML front matter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            metadata = yaml.safe_load(parts[1])
            if 'date-modified' in metadata and metadata['date-modified'] == "last-modified":
                metadata['date-modified'] = last_modified
                new_content = f"---\n{yaml.safe_dump(metadata)}---{parts[2]}"
                with open(file, 'w') as f:
                    f.write(new_content)

# Apply the function to all .qmd files
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.qmd'):
            update_date_modified(os.path.join(root, file))

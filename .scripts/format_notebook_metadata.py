import nbformat
import glob
import yaml
import os

for ipynb_path in glob.glob('Learn/Notebooks/**/*.ipynb', recursive=True):
    qmd_path = ipynb_path.replace('.ipynb', '.qmd')
    if not os.path.exists(qmd_path):
        continue

    with open(qmd_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Parse YAML front matter
    if lines[0].strip() != '---':
        continue
    yaml_end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == '---')
    yaml_block = ''.join(lines[1:yaml_end])
    metadata = yaml.safe_load(yaml_block)

    title = metadata.get("title", "")
    authors = metadata.get("author", [])
    author_str = ', '.join(f'{a.get("name", "")} ({a.get("email", "")})' for a in authors)
    date = metadata.get("date", "")
    categories = metadata.get("categories", [])

    html_url = f"https://uw-madison-datascience.github.io/ML-X-Nexus/Learn/Notebooks/{os.path.basename(ipynb_path).replace('.ipynb', '.html')}"

    meta_md = f"""# {title}
### {author_str}
### [{html_url}]({html_url})
### Categories
{chr(10).join(f"- {cat}" for cat in categories)}
"""

    with open(ipynb_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    if nb.cells and nb.cells[0].cell_type == 'markdown':
        src = nb.cells[0].source.strip()
        if src.startswith('---'):
            parts = src.split('---')
            intro_text = '---'.join(parts[2:]).strip()
            nb.cells[0] = nbformat.v4.new_markdown_cell(intro_text) if intro_text else nb.cells.pop(0)

    nb.cells.insert(0, nbformat.v4.new_markdown_cell(meta_md))

    with open(ipynb_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)

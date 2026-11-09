"""Quarto post-render step: show resource authors on listing tiles.

Tiles can only print a page's `author` (the Nexus author). For pages that set
`resource-author` (the makers of a book, talk, lesson or competition the page
shares), this swaps the tile's author line for those names, in every rendered
listing. The page itself still shows both in its title block.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FM = re.compile(r"\A---\n(.*?)\n---", re.S)
RA = re.compile(r"^resource-author:[^\n]*\n((?:[ \t]+-[^\n]*\n)+)", re.M)
ITEM_START = re.compile(r'<div class="(?:g-col-1|quarto-post)[ "]')
HREF = re.compile(r'href="([^"]+\.html)(?:#[^"]*)?"')
AUTHOR = re.compile(r'(<div class="listing-author">)(.*?)(</div>)', re.S)


def resource_authors():
    out = {}
    for dirpath, _, names in os.walk(ROOT):
        if "/." in dirpath or "/_" in dirpath:
            continue
        for n in names:
            if not n.endswith(".qmd"):
                continue
            path = os.path.join(dirpath, n)
            with open(path, encoding="utf-8") as fh:
                m = FM.match(fh.read())
            if not m:
                continue
            ra = RA.search(m.group(1))
            if not ra:
                continue
            names_ = [re.sub(r'^\s*-\s*"?(.*?)"?\s*$', r"\1", line) for line in ra.group(1).splitlines() if line.strip()]
            rel = os.path.relpath(path, ROOT)[:-4] + ".html"
            out[rel] = ", ".join(names_)
    return out


def fix_listing(html, page_dir, authors):
    starts = [m.start() for m in ITEM_START.finditer(html)]
    if not starts:
        return html
    pieces, prev = [html[: starts[0]]], starts[0]
    for nxt in starts[1:] + [len(html)]:
        seg = html[prev:nxt]
        h = HREF.search(seg)
        if h:
            target = os.path.normpath(os.path.join(page_dir, h.group(1)))
            if target in authors:
                seg = AUTHOR.sub(lambda m: f"{m.group(1)}\n{authors[target]}\n{m.group(3)}", seg, count=1)
        pieces.append(seg)
        prev = nxt
    return "".join(pieces)


def main() -> int:
    out_dir = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "_site")
    files = [f for f in os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").split("\n") if f.endswith(".html")]
    if not files:
        files = [os.path.join(r, n) for r, _, ns in os.walk(out_dir) for n in ns if n.endswith(".html")]
    authors = resource_authors()
    changed = 0
    for path in files:
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        if "listing-author" not in html:
            continue
        rel_dir = os.path.dirname(os.path.relpath(os.path.abspath(path), os.path.abspath(out_dir)))
        new = fix_listing(html, rel_dir, authors)
        if new != html:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
            changed += 1
    print(f"tile_resource_authors: {len(authors)} pages with resource authors; updated {changed} listing file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

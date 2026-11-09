"""Quarto post-render step: drop blank "other field" rows from grid listing tiles.

Quarto fills a listed field that a page does not set with a non-breaking space,
so every tile would otherwise show an empty "Created by" row. This removes any
card-other-values row whose value cell is blank, in every rendered HTML file.
"""
import os
import re
import sys

ROW = re.compile(
    r"\s*<tr>\s*<td>\s*[^<]*?\s*</td>\s*<td class=\"[^\"]*\">\s*(?:&nbsp;| )?\s*</td>\s*</tr>",
    re.S,
)


def main() -> int:
    files = [f for f in os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").split("\n") if f.endswith(".html")]
    out_dir = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "_site")
    if not files:  # not run by Quarto: walk the output directory instead
        files = [os.path.join(r, n) for r, _, ns in os.walk(out_dir) for n in ns if n.endswith(".html")]
    changed = 0
    for path in files:
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        if "card-other-values" not in html:
            continue
        new = ROW.sub("", html)
        if new != html:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
            changed += 1
    print(f"strip_blank_listing_rows: cleaned {changed} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

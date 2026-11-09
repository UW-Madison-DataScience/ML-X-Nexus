# CLAUDE.md

## Repository Rules

- **NEVER edit `.ipynb` files.** Notebooks are auto-generated from `.qmd` files. Only edit the `.qmd` source files.

## Writing Rules


- Never use the word "real" as an intensifier ("a real task", "real research", "real-world"). Say what the thing is instead.
- No colloquial openers or hedging adverbs ("surprisingly", "simply", "the trick is"). State the fact.
- Maintainer notes go in an HTML comment at the top of the file, never in reader-facing text.
- Tile pages for externally hosted material follow the same sections as the other tiles: Prerequisites, Estimated time to complete, Related resources (bulleted, with bold type prefixes), Comments.
- Reference figures from an upstream lesson by their published URL; do not copy them into `images/` unless the file is specific to this site (for example, a cropped tile image).

## Dates

- `date-modified` marks a change in a page's substance: facts, numbers, recommendations, instructions, prerequisites, scope or structure. Set it to today when you make such a change. Leave it alone for typos, wording, formatting, tags, links and cross-references.
- An Action re-checks every push to main and moves the date when the change was substantive. Put `[minor]` in a commit message to tell it not to, or `[content]` to make it.
- Lesson tiles with `lesson-repo` take their date from the upstream repository; pages with `date-modified-auto: false` are pinned by hand. Do not edit those dates.

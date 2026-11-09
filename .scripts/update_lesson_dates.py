"""Set date-modified on tile pages from their upstream lesson repository.

A tile page (a .qmd) that points at a lesson hosted elsewhere declares the
repository in its YAML front matter:

    lesson-repo: carpentries-incubator/ML_with_AWS_SageMaker

For each such page, this script asks the GitHub API for the date of the
repository's latest commit on its default branch and writes it to the page's
`date-modified:` line (adding the line after `date:` if there is none). Pages
without `lesson-repo` are left alone. Run from the repository root:

    python3 .scripts/update_lesson_dates.py            # update files in place
    python3 .scripts/update_lesson_dates.py --dry-run  # report only

GITHUB_TOKEN, if set, is sent as a bearer token to raise the API rate limit.
"""
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

API = "https://api.github.com/repos/{repo}/commits?per_page=1"
FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def latest_commit_date(repo):
    req = urllib.request.Request(API.format(repo=repo), headers={"Accept": "application/vnd.github+json",
                                                                 "User-Agent": "ML-X-Nexus-lesson-dates"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    return data[0]["commit"]["committer"]["date"][:10]   # YYYY-MM-DD


def update_page(path, dry_run):
    text = open(path, encoding="utf-8").read()
    m = FRONT.match(text)
    if not m:
        return None
    front = m.group(1)
    rm = re.search(r"^lesson-repo:\s*([\w.-]+/[\w.-]+)\s*$", front, re.M)
    if not rm:
        return None
    repo = rm.group(1)
    try:
        date = latest_commit_date(repo)
    except (urllib.error.URLError, KeyError, IndexError, ValueError) as e:
        print(f"SKIP  {path}: could not read {repo} ({e})")
        return False
    if re.search(r"^date-modified:", front, re.M):
        new_front = re.sub(r"^date-modified:.*$", f"date-modified: {date}", front, count=1, flags=re.M)
    elif re.search(r"^date:", front, re.M):
        new_front = re.sub(r"^(date:.*)$", rf"\1\ndate-modified: {date}", front, count=1, flags=re.M)
    else:
        new_front = front + f"\ndate-modified: {date}"
    if new_front == front:
        print(f"OK    {path}: {repo} last modified {date} (unchanged)")
        return False
    print(f"{'WOULD' if dry_run else 'SET  '} {path}: {repo} last modified {date}")
    if not dry_run:
        open(path, "w", encoding="utf-8").write(text[:m.start(1)] + new_front + text[m.end(1):])
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    paths = [a for a in sys.argv[1:] if not a.startswith("--")] or sorted(glob.glob("**/*.qmd", recursive=True))
    changed = sum(bool(update_page(p, dry_run)) for p in paths)
    print(f"{changed} page(s) {'would change' if dry_run else 'changed'}")


if __name__ == "__main__":
    main()

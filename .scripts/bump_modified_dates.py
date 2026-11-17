"""Bump date-modified on pages whose content changed in substance.

Run after a push to main with the range of commits it brought:

    python3 .scripts/bump_modified_dates.py <base-sha> <head-sha> [--dry-run]

For every content page (.qmd) changed in the range, the script compares the
page's body before and after. The comparison ignores the YAML front matter,
code blocks, HTML comments and tags, link targets and bare URLs, headings, the
"Related resources" and "Comments" sections, and list items that are only a
link. What remains is the prose, tables and lists a reader learns from.

Decision, in order:
  1. A commit message in the range with [content] forces a bump; [minor]
     suppresses one (for the files that commit touched).
  2. Otherwise, if ANTHROPIC_API_KEY is set, a Claude model reads the body diff
     and answers whether the substance changed: facts, numbers, recommendations,
     instructions, scope or structure, as opposed to wording, typos, formatting,
     tags or cross-references. Below SMALL_CHANGE changed words the model is not
     asked and the change is treated as editorial.
  3. Without a key, a word-count heuristic decides: at least MIN_WORDS words
     added or removed and at least MIN_FRACTION of the body.

Pages are skipped when they declare `lesson-repo` (their date comes from the
upstream repository) or `date-modified-auto: false` (pinned by hand), and
commits by bots are ignored. A qualifying page gets date-modified set to the
date of the latest qualifying commit, if newer than its current value.
"""
import difflib
import json
import os
import re
import subprocess
import sys

SMALL_CHANGE = 8      # changed words below which no page is judged substantive
MIN_WORDS = 25        # heuristic fallback: words added + removed
MIN_FRACTION = 0.02   # heuristic fallback: of the page's body words
BOTS = ("github-actions", "quarto-bot", "dependabot")
SKIP_PREFIX = ("Contributor-templates/", "includes/", ".")
MODEL = "claude-opus-5-5"

JUDGE_INSTRUCTIONS = """You review edits to pages on a university machine-learning resource site and decide whether a page's last-modified date should move.

The date moves only for a change in substance: facts, numbers, dates, recommendations, instructions, prerequisites, the set of topics covered, or the page's structure in a way that changes what a reader learns or does. It does not move for rewording that preserves meaning, typo and grammar fixes, formatting, punctuation, heading renames, tag or category changes, link additions or repointing, cross-references, or attribution and contact changes.

You are given the page title and a word-level diff of the page body (front matter, links and navigation sections already removed). Decide and explain in one sentence."""

JUDGE_SCHEMA = {"type": "object",
                "properties": {"substantive": {"type": "boolean"}, "reason": {"type": "string"}},
                "required": ["substantive", "reason"], "additionalProperties": False}


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def body_text(text):
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end > 0:
            text = text[end + 5:]
    text = re.sub(r"\n## Related resources\b.*?(?=\n## |\Z)", "\n", text, flags=re.S | re.I)
    text = re.sub(r"\n## Comments\b.*?(?=\n## |\Z)", "\n", text, flags=re.S | re.I)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"^\s*[-*]\s*\[[^\]]*\]\([^)]*\)\s*$", " ", text, flags=re.M)   # link-only list items
    text = re.sub(r"\]\([^)]*\)", "]", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"^#{1,6}\s.*$", " ", text, flags=re.M)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def words(text):
    return re.findall(r"[A-Za-z0-9][\w'’.%-]*", text)


def word_diff(old, new):
    a, b = words(old), words(new)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    changed, pieces = 0, []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        changed += max(i2 - i1, j2 - j1)
        if i2 > i1:
            pieces.append("- " + " ".join(a[i1:i2]))
        if j2 > j1:
            pieces.append("+ " + " ".join(b[j1:j2]))
    return changed, max(len(a), len(b), 1), "\n".join(pieces)


def judge_with_claude(title, diff):
    import anthropic
    client = anthropic.Anthropic()
    try:
        r = client.messages.create(
            model=MODEL, max_tokens=1024, system=JUDGE_INSTRUCTIONS,
            messages=[{"role": "user", "content": f"Page: {title}\n\nBody diff (- removed, + added):\n{diff[:12000]}"}],
            output_config={"format": {"type": "json_schema", "schema": JUDGE_SCHEMA}},
        )
    except anthropic.APIError as e:
        print(f"      judge unavailable ({e.__class__.__name__}); using word count")
        return None
    if r.stop_reason == "refusal" or not r.content or r.content[0].type != "text":
        return None
    try:
        out = json.loads(r.content[0].text)
    except json.JSONDecodeError:
        return None
    return bool(out["substantive"]), out.get("reason", "")


def main():
    base, head = sys.argv[1], sys.argv[2]
    dry = "--dry-run" in sys.argv
    use_llm = bool(os.environ.get("ANTHROPIC_API_KEY"))
    commits = [l.split("\t") for l in git("log", "--format=%H\t%as\t%an\t%s", f"{base}..{head}").splitlines()]
    files = {}
    for sha, date, author, subject in reversed(commits):
        if any(b in author.lower() for b in BOTS):
            continue
        for path in git("diff-tree", "--no-commit-id", "--name-only", "-r", sha).splitlines():
            if not path.endswith(".qmd") or path.startswith(SKIP_PREFIX) or path.split("/")[-1] == "index.qmd":
                continue
            f = files.setdefault(path, {"date": date, "force": False, "minor": False})
            f["date"] = max(f["date"], date)
            f["force"] |= "[content]" in subject
            f["minor"] |= "[minor]" in subject
    bumped = 0
    for path, f in sorted(files.items()):
        try:
            new = git("show", f"{head}:{path}")
        except subprocess.CalledProcessError:
            continue
        fm_end = new.find("\n---\n", 4)
        fm = new[4:fm_end] if new.startswith("---\n") and fm_end > 0 else ""
        if re.search(r"^lesson-repo:", fm, re.M) or re.search(r"^date-modified-auto:\s*false", fm, re.M):
            print(f"skip  {path}: date managed elsewhere"); continue
        if not re.search(r"^date:", fm, re.M):
            continue
        try:
            old = git("show", f"{base}:{path}")
        except subprocess.CalledProcessError:
            print(f"new   {path}: new page, publication date stands"); continue
        n, total, diff = word_diff(body_text(old), body_text(new))
        title = (re.search(r'^title:\s*"?(.*?)"?\s*$', fm, re.M) or [None, path])[1]
        reason = ""
        if f["force"]:
            substantive, reason = True, "[content] in commit message"
        elif f["minor"]:
            substantive, reason = False, "[minor] in commit message"
        elif n < SMALL_CHANGE:
            substantive, reason = False, f"{n} words changed"
        else:
            verdict = judge_with_claude(title, diff) if use_llm else None
            if verdict is None:
                substantive = n >= MIN_WORDS and n / total >= MIN_FRACTION
                reason = f"word count: {n} of {total} ({100*n/total:.1f}%)"
            else:
                substantive, reason = verdict
        print(f"{'BUMP ' if substantive else 'keep '} {path}: {reason}")
        if not substantive:
            continue
        cur = re.search(r"^date-modified:\s*(\d{4}-\d{2}-\d{2})", fm, re.M)
        if cur and cur.group(1) >= f["date"]:
            continue
        if cur:
            updated = re.sub(r"^(date-modified:\s*)\d{4}-\d{2}-\d{2}", rf"\g<1>{f['date']}", new, count=1, flags=re.M)
        else:
            updated = re.sub(r"^(date:.*\n)", rf"\1date-modified: {f['date']}\n", new, count=1, flags=re.M)
        if not dry:
            open(path, "w", encoding="utf-8").write(updated)
        bumped += 1
        print(f"      -> date-modified: {f['date']}")
    print(f"{bumped} page(s) {'would be ' if dry else ''}bumped")


if __name__ == "__main__":
    main()

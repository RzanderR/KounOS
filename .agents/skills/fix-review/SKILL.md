---
name: fix-review
description: Address a failed KounOS review on an open pull request, push the fixes to the same branch, and reply to the review. Use when asked to fix review findings, for example "/fix-review 12".
---

# Fix a failed review

You are the builder. Claude Code reviewed your pull request and posted a comment starting `KounOS review: fail` with a scorecard. Fix what blocks the merge, then stop.

## 1. Load the review

- Get the pull request number from the request. Read its latest `KounOS review:` comment (for example with `gh pr view <number> --comments`).
- If the latest review says `pass`, report that there is nothing to fix and stop.
- Count earlier `KounOS review: fail` comments on this pull request. If this would be the fourth round, **stop**: report that the task needs a human decision.

## 2. Fix

- Check out the pull request's branch. Do not create a new branch or a new pull request.
- Fix every item in the scorecard's `blocking` list. Take a `suggestions` item only if it is small and inside the brief's scope.
- If you disagree with a blocking item, or fixing it needs something outside the brief, do not change the code for it. Explain why in your reply instead.
- Keep every rule in `AGENTS.md` and the brief's scope.

## 3. Check

- Rerun every check in the brief and in `AGENTS.md`. Fix and rerun; after three failed attempts on the same check, stop and report it.

## 4. Reply and stop

- Commit, push to the same branch, never force-push.
- Reply on the pull request with one line per blocking item: what you changed and the commit, or why you didn't.
- Report back with the pull request link and what changed, then stop. Claude Code reviews again.

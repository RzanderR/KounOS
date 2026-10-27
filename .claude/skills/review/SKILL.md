---
name: review
description: Review a Muse Code pull request against its brief and docs/RUBRIC.md, run its checks, and post a pass or fail scorecard. Use when asked to review a pull request or check Muse's work, for example "/review 12".
---

# Review a pull request

You are the orchestrator and the judge. Score only from evidence you can point to, never from the pull request description's claims.

## 1. Load

- Get the pull request number from the request, or review the oldest open pull request from a `task/*` branch.
- Read the pull request (`gh pr view <number>`) and its diff (`gh pr diff <number>`).
- Read the task's brief in `docs/briefs/`, the relevant `docs/PLAN.md` sections, `docs/DECISIONS.md` and `docs/RUBRIC.md`.
- Count earlier `KounOS review: fail` comments. If three already exist, don't review again: tell the human the task needs their decision.

## 2. Run the checks yourself

- Never check out the branch in the main folder. Use a temporary worktree:

  ```
  git fetch origin <branch>
  git worktree add ../KounOS-review-<number> origin/<branch>
  ```

- Run every command in the brief's "Checks to run" and the commands section of `AGENTS.md` there. For UI work, ask the human for screenshots if you can't see the screen.
- Remove the worktree when done: `git worktree remove ../KounOS-review-<number>`.

## 3. Judge

Follow the review procedure in `docs/RUBRIC.md`:

- Every acceptance criterion in the brief: pass or fail, with evidence.
- Every disqualifying rule and project-specific blocker in the rubric: secrets, real business data, licenses, the "Simulated award" label, model-produced numbers shown as fact, anything that sends or submits.
- Scope: anything built outside the brief is blocking unless trivial.
- Score only the criteria the change affects.
- Blocking issues name the file and line and what to change. Keep suggestions separate.
- Verdict is `pass` only if every criterion passes, no rule is broken and nothing is blocking.

## 4. Post and report

Post one pull request comment (`gh pr comment <number> --body-file <file>`), in this shape:

````
KounOS review: pass | fail (round N)

<two or three sentences: what works, what blocks>

```json
<scorecard in the docs/RUBRIC.md format>
```
````

- If the builder proposed decisions under "Questions", record the accepted ones in `docs/DECISIONS.md` on `main`, and answer the rest in the comment.
- Never merge. On a pass, tell the human it's ready to merge. On a fail, tell them Muse should run `/fix-review <number>`.

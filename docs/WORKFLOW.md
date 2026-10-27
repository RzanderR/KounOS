# Build workflow: Claude Code designs, Muse Code builds

How the two agents and the human hand work to each other. `AGENTS.md` points here; when the two disagree, this file wins for anything about the handoff.

## Roles

| Who | Does | Does not |
| --- | --- | --- |
| **Human** | Makes decisions, does the H tasks, ticks gates, merges pull requests | Get surprised: every agent stop lands in chat or on a pull request |
| **Claude Code** (orchestrator) | Writes a brief for each task, reviews every pull request against its brief and `docs/RUBRIC.md`, keeps `docs/PLAN.md`, `TASKS.md` and `docs/DECISIONS.md` current | Write product code (it may fix docs and config) |
| **Muse Code** (builder) | Builds one brief at a time on a task branch, opens a pull request, fixes review findings | Change scope, the plan, the rubric, the briefs or the decisions log; merge |

## The cycle

```
Brief (Claude) -> Build (Muse) -> Review (Claude) -> Fix (Muse) -> Merge (human)
                                      ^                 |
                                      +-----------------+   at most 3 rounds
```

1. **Brief.** Claude Code runs `/brief`. It writes `docs/briefs/<ID>.md` from `docs/briefs/TEMPLATE.md` and commits briefs straight to `main` (they are docs only).
2. **Build.** Muse Code runs `/next-task`. It picks the next ready brief, builds it on `task/<ID>-<short-name>`, runs the checks and opens a pull request using `.github/pull_request_template.md`.
3. **Review.** Claude Code runs `/review <PR number>`. It posts one comment starting `KounOS review: pass` or `KounOS review: fail`, followed by the scorecard from `docs/RUBRIC.md`.
4. **Fix.** On a fail, Muse Code runs `/fix-review <PR number>` and pushes fixes to the same branch. Then back to review.
5. **Merge.** On a pass, the human merges. The task's tick in `TASKS.md` lands with it.

After three failed review rounds on one task, both agents stop and the human decides: re-brief, split the task, or accept it as is.

## State lives in the repo

| You see | It means |
| --- | --- |
| `docs/briefs/<ID>.md` with `Status: ready`, task unchecked in `TASKS.md` | Ready to build |
| `docs/briefs/<ID>.md` with `Status: blocked` | Waiting on a human task, a gate or a decision; the reason is in the brief |
| An open pull request from `task/<ID>-*` | Built, waiting for review or fixes |
| Latest review comment says `KounOS review: pass` | Ready for the human to merge |
| Task ticked in `TASKS.md` on `main` | Done |

## Where each agent works

The agents must not switch branches under each other, so each gets its own folder:

- **Claude Code** works in `KounOS/` on `main`, writing briefs and reviewing. To run a pull request's checks it uses a temporary worktree, never a checkout of the main folder.
- **Muse Code** works in a second clone, for example `KounOS-build/` next to `KounOS/`:

  ```
  git clone https://github.com/RzanderR/KounOS ../KounOS-build
  ```

  Muse creates its own worktrees for subagents inside that clone.

Push everything on `main` before Muse starts, so its clone has the latest briefs.

## Muse stops and reports, instead of guessing, when

- The next task is a human (H) task or sits behind a gate that isn't ticked
- No brief exists, or the brief says `Status: blocked`
- The brief conflicts with `docs/PLAN.md`, `docs/RUBRIC.md` or `AGENTS.md`, or is ambiguous
- The work needs a dependency, file or change the brief doesn't cover
- A check still fails after three fix attempts
- A task has failed review three times

When it stops, it says which rule it hit and what it needs, in the pull request if one exists, otherwise in chat.

## Unattended runs

Muse can run one cycle at a time without a person watching:

```
muse exec --json "/next-task"
```

One task per run. It never merges, never pushes to `main`, and keeps approval prompts on (never `--yolo` on a personal machine). Review the pull requests when you're back.

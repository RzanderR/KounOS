# Build workflow: human and Muse Code, direct

One builder, no handoffs. The human decides and supplies; Muse Code designs (inline), builds, checks, and opens pull requests. No briefs required, no review rounds.

## Roles

| Who | Does | Does not |
| --- | --- | --- |
| **Human** | Decides scope, does the H tasks, supplies contracts/quotes/keys, ticks gates, merges pull requests | Get surprised: every stop lands in chat or on a pull request |
| **Muse Code** (builder) | Builds one task per run on a task branch, runs the checks, opens a pull request | Merge, push to `main`, force-push, or commit secrets/real business data |

## The cycle

```
Ask (human) -> Build (Muse) -> Check (Muse) -> Pull request (Muse) -> Merge (human)
```

1. **Ask.** The human picks the next `TASKS.md` item or describes the work directly. Human words win over backlog order.
2. **Build.** Muse works on `task/<ID>-<short-name>` from `origin/main`. Push the branch early and often, even half done; the branch is the backup. For anything bigger than a small change, it writes the spec inline (files, checks, acceptance) in the pull request description — no separate brief required. Existing `docs/briefs/` are history and optional reference.
3. **Check.** Muse runs every relevant check (the commands section of `AGENTS.md`, plus task-specific tests) and reports the evidence. A check that cannot run in the sandbox is reported, not worked around.
4. **Pull request.** One task per PR, using `.github/pull_request_template.md`, with evidence for each acceptance criterion. Muse self-checks the hard rules in `AGENTS.md` before opening.
5. **Merge.** The human merges. The task's tick in `TASKS.md` lands with it.

## Quality without the queue

- Spot skills, on demand: `/to-spec` (spec a big task), `/implement`, `/code-review` (two-axis self-check of a diff), `surgical-patch`, `verify-and-stop`, `/retro` (close the loop after a build). `ask-matt` routes to the right flow.
- Style modes: `/caveman` and `ponytail` change how Muse writes and replies; they do not change what gets built.
- `fix-review` answers any `KounOS review:` comment on an open pull request, whoever posted it.

## Gates and data rules (still human)

- Gate 1/2/3 in `TASKS.md` are human confirmations. No work starts past a gate until the human ticks it.
- Real supplier quotes and real business data enter the repo only with the human's explicit say-so, labeled per the `AGENTS.md` hard rules (written permission on file, labeled real). Fictional data stays labeled fictional.

## State lives in the repo

| You see | It means |
| --- | --- |
| Task unchecked in `TASKS.md`, no open PR from `task/<ID>-*` | Ready to build |
| An open pull request from `task/<ID>-*` | Built, waiting for merge or fixes |
| Task ticked in `TASKS.md` on `main` | Done |

## Where the work happens

Muse Code works in `KounOS-muse/` (a worktree of this repo) and never switches branches in the main checkout. One task branch at a time.

## Muse stops and reports, instead of guessing, when

- The task is a human (H) task or sits behind a gate that isn't ticked
- The request is ambiguous, or conflicts with `docs/PLAN.md`, `docs/RUBRIC.md` or `AGENTS.md`
- The work needs a dependency, file or change the request doesn't cover
- A check still fails after three fix attempts
- A secret or real business data would have to be committed to proceed

When it stops, it says which rule it hit and what it needs, in the pull request if one exists, otherwise in chat.

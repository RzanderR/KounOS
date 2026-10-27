# <ID>: <title>

Status: ready | blocked (<why, and what unblocks it>)
Depends on: <task IDs and gates that must be done first, or "none">
Task in TASKS.md: <ID>

## Goal

One paragraph: what this task delivers and why it matters for the demo story or the rubric.

## Scope

**In:**
- ...

**Out** (do not build these here):
- ...

## Design

**Files and owners** (one owner per file, so subagents don't collide):

| File or folder | Owner | What goes in it |
| --- | --- | --- |
| `api/...` | subagent 1 | ... |

**Interfaces:** schemas, function signatures, routes and response shapes other tasks depend on.

**Key logic:** the approach, in a few bullets. Name the edge cases.

**Dependencies:** new libraries allowed for this task, with their licenses. Nothing else may be added.

## Acceptance criteria

Each one checkable, with the evidence the review should see:

- [ ] ... (evidence: test name, command output, screenshot)

## Test vectors

Exact inputs and expected outputs for money, date and extraction logic.

| Input | Expected |
| --- | --- |
| ... | ... |

## Checks to run

```
<exact commands>
```

## References

- `docs/PLAN.md`: <section>
- `docs/DECISIONS.md`: <D numbers>

---
name: brief
description: Write implementation briefs in docs/briefs/ for upcoming KounOS tasks so Muse Code can build them. Use when asked to plan, design or prepare the next tasks, or to brief specific task IDs.
---

# Brief the next tasks

You are the orchestrator. You design; Muse Code builds from what you write. A good brief lets a builder finish the task without asking a question. Read `docs/WORKFLOW.md` for the full cycle.

## 1. Load context

- Read `AGENTS.md`, `docs/WORKFLOW.md`, `docs/PLAN.md`, `docs/RUBRIC.md`, `docs/DECISIONS.md` and `TASKS.md`.
- Look at the code that exists on `main` and at open pull requests, so briefs fit what is actually there.

## 2. Choose tasks

- If task IDs were given, brief those. Otherwise brief the next one to three unchecked **A** tasks in `TASKS.md` that have no brief yet.
- A task whose inputs depend on an unfinished human task or an unticked gate still gets a brief, marked `Status: blocked` with the exact reason and what unblocks it.

## 3. Write each brief

Copy `docs/briefs/TEMPLATE.md` to `docs/briefs/<ID>.md` and fill in every section:

- **Concrete, not abstract.** Exact file paths, function and route names, schema fields, response shapes and the commands to run.
- **One owner per file**, so Muse's subagents don't collide. Shared contracts (schemas, types) belong to one owner and are built first.
- **Test vectors from the plan.** Money, dates and extraction get exact inputs and expected outputs, using `docs/PLAN.md` numbers and `docs/DECISIONS.md` D01 (placeholder quote amounts until H03 is done).
- **Acceptance criteria a reviewer can check**, each with the evidence expected.
- **Scope out** lists what not to build, especially anything a later task owns.
- **Dependencies:** name any new library and its license; only MIT, BSD, Apache-2.0 or ISC.
- **Size:** one pull request, roughly under 400 changed lines of code. If a task is bigger, split it into `<ID>a`, `<ID>b` in `TASKS.md` and brief each.

## 4. Stay inside the plan

- A brief may make implementation choices. Record any choice later tasks depend on as a new `D<number>` entry in `docs/DECISIONS.md`.
- If a design would change scope, the demo story or a rule, do not write it into a brief. Ask the human first.
- Do not write product code.

## 5. Commit and report

- Commit the briefs (and any `TASKS.md` or `docs/DECISIONS.md` changes) to `main` with a message like `Brief A04-A06`, and push.
- Tell the human which tasks are ready for Muse, which are blocked and why, and anything you need them to decide.

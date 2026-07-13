---
name: project-continuity-handoff
description: "Recover, verify, and summarize ongoing project state across Hermes sessions before continuing work."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [project-continuity, handoff, session-search, memory, status]
    created_by: agent
---

# Project Continuity & Handoff

Use this skill when the user asks about the current progress of an ongoing project, says to inherit/continue previous work, asks "where are we?", "what is left?", or corrects the agent for acting on the wrong thread of work.

The goal is to reconstruct the true state from durable sources and live checks, then give a concise status summary and next action. Do **not** pivot into a nearby workflow just because a keyword appears (for example, "PR" does not override an active project-status question unless the user explicitly asks to create/push/open the PR now).

## Workflow

1. **Identify the project thread first.**
   - Use current conversation context, persistent memory, JiuwenMemory, and session history to identify the named project/task.
   - If the user says "不对" / "that's not it", immediately stop the current interpretation and re-anchor on the topic they name.

2. **Search historical context before asking the user to repeat themselves.**
   - Use session search for project names, branch names, benchmark names, feature names, and "remaining tasks" language.
   - Use memory search when available for compact durable facts.
   - Prefer newest relevant sessions, but verify whether a prior "remaining item" has since been completed.

3. **Verify live state where possible.**
   - For services: check health endpoints and service status.
   - For repositories: check current branch, recent commits, remotes, and auth/push state.
   - For benchmarks: find actual recorded metrics or rerun if required by the user.

4. **Separate status layers.**
   Report these distinctly instead of mixing them:
   - Runtime/service health
   - Feature/PoC implementation and test status
   - Benchmark/metric status
   - Code persistence/branch/PR status
   - Remaining productization/hardening work

5. **Be concise but grounded.**
   - Include exact evidence snippets only where they clarify the state.
   - Do not narrate the whole prior session.
   - End with the real next blocker or next executable step.

## Pitfalls

- **Wrong-thread pivot:** If a user asks "能不能构建PR？" after a progress thread, this may mean "can this work be made into a PR?" not "start generic GitHub PR setup." Check repo/auth only after anchoring the project.
- **Stale remaining tasks:** A task that was previously listed as remaining may have been completed later. Search both session history and memory before saying it remains.
- **Unverified PR status:** SSH/auth success is not equivalent to PR creation. Distinguish "branch committed", "pushed to fork", and "PR opened".
- **Protected skills:** If the relevant procedural skill is bundled/protected, do not edit it; create or update an agent-owned umbrella skill instead.

## Output Template

```markdown
## 当前状态
- Runtime: ...
- Features/tests: ...
- Benchmarks: ...
- Code/PR: ...

## 还剩什么
1. ...
2. ...

## 下一步
...single concrete action...
```

## References

- `references/jiuwenmemory-progress-handoff.md` — example of reconstructing a JiuwenMemory project handoff from memory, session history, live service checks, and git state.

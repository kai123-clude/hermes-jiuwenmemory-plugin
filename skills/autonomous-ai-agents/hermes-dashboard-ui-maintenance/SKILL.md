---
name: hermes-dashboard-ui-maintenance
description: "Maintain and debug Hermes Dashboard UI flows, especially Chat/Sessions history rendering, profile-scoped session lists, and frontend verification."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, dashboard, react, sessions, chat, verification]
    related_skills: [hermes-agent]
---

# Hermes Dashboard UI Maintenance

Use this skill when changing or debugging Hermes Dashboard web UI behavior (`web/src/**`, `hermes_cli/web_server.py` API surfaces, embedded Chat, Sessions page, profile-scoped dashboard state).

## Core workflow

1. **Clarify the exact surface before coding.** Hermes has several session-history surfaces that look similar:
   - Chat page right rail: `web/src/components/ChatSessionList.tsx`
   - Chat page resumed transcript / embedded terminal: `web/src/pages/ChatPage.tsx`
   - Sessions management page: `web/src/pages/SessionsPage.tsx`
   - Backend session endpoints: `hermes_cli/web_server.py`
2. **Reproduce with the Dashboard when possible.** Start a local dashboard, open the target route, click the same UI the user describes, then refresh the page to test reload behavior.
3. **Prefer DB-backed history for persisted conversations.** Do not rely on xterm/PTY scrollback to show old conversation contents after browser refresh. For resumed sessions, fetch persisted messages from the session DB (`/api/sessions/<id>/messages`) and render them independently of the live PTY.
4. **Respect profile scope.** If a UI can be used after refresh or across profile changes, verify whether it should call profile-specific endpoints or the unified profile aggregator (`/api/profiles/sessions`). Profile state may not be initialized the same way before and after a refresh.
5. **Keep UI fixes narrow.** Reuse existing components (`SessionRow`, shared API helpers, existing Markdown renderers) rather than creating parallel implementations unless the UX genuinely differs.

## Pitfalls

- User reports like “old conversations don’t show” may mean the **Chat right rail + center transcript**, not the Sessions page. Ask only if needed; otherwise inspect both surfaces and name which one you are fixing.
- A right-rail session title list can be correct while the main chat content is empty. That usually means navigation/session listing works, but persisted message rendering or resume behavior is missing.
- Browser refresh is a first-class test case. If reload clears the visible transcript, the fix is incomplete even if clicking a session works before refresh.
- For `/chat?resume=<id>`, keep-alive PTY attach tokens must be scoped by resume id/profile. A single browser-wide `?attach=` token can reattach the previous fresh PTY and silently ignore the new `?resume`, leaving old-session clicks looking empty or stale.
- Do not claim a dashboard UI fix is done from TypeScript alone. Build the web bundle and, when practical, verify via browser automation.

## Verification checklist

Run the smallest relevant set, then broaden if failures suggest cross-cutting impact:

```bash
cd ~/.hermes/hermes-agent/web
npm run typecheck
npx eslint <changed files>
npm test -- <relevant test file or pattern>
npm run build
```

For Chat/Sessions history fixes, also verify manually or with browser automation:

1. Open `/chat`.
2. Confirm the right rail lists historical sessions.
3. Click an older session.
4. Confirm persisted content appears in the main area.
5. Refresh the browser.
6. Confirm the right rail and persisted content still appear.

See `references/chat-session-history-refresh.md` for the concrete pattern learned from the old-conversation-history bug.
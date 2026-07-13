# Chat session history after refresh

Context: The user reported that the Chat page right-side conversation rail still showed historical conversation titles, but clicking them produced an empty main conversation area after refresh. The key correction was that this was **not** primarily the Sessions management page; it was the Dashboard Chat surface.

## Surfaces involved

- Right rail session switcher: `web/src/components/ChatSessionList.tsx`
- Main Chat page transcript/PTY area: `web/src/pages/ChatPage.tsx`
- API client: `web/src/lib/api.ts`
- Backend list/detail/messages endpoints: `hermes_cli/web_server.py`

## Durable fix pattern

1. Keep the right rail as navigation, but make its session listing robust after refresh/profile changes.
   - Use `/api/profiles/sessions` when a unified/profile-aware session list is needed.
   - Add a typed API helper rather than hand-building fetches inside components.
2. Treat persisted transcript display separately from live terminal scrollback.
   - On `/chat?resume=<session_id>`, fetch `/api/sessions/<id>/messages`.
   - Render saved messages in a read-only history panel so old content is visible even if the PTY/xterm buffer is empty after refresh.
3. Verify the actual user path:
   - open `/chat`
   - confirm right rail titles are present
   - click an old conversation
   - confirm saved message content appears
   - press refresh/F5
   - confirm the same content still appears

## Verification commands used

```bash
cd ~/.hermes/hermes-agent/web
npm run typecheck
npx eslint src/components/ChatSessionList.tsx src/lib/api.ts
npm test -- session-transcript.test.ts
npm run build
```

Notes:

- Linting only changed files can pass even if a larger legacy file has unrelated hook lint debt. Report that distinction explicitly.
- If a system reminder asks for fresh verification after edits, rerun the relevant commands immediately; do not merely cite earlier output.
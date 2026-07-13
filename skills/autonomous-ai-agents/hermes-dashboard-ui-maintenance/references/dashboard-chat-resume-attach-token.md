# Dashboard Chat resume + keep-alive PTY attach tokens

Session learning: clicking an old Chat session can still show an empty/stale main terminal even when `/chat?resume=<id>` is correct if the browser reuses the same keep-alive PTY `?attach=` token that was used for a fresh chat.

## Symptom

- Right rail shows historical sessions.
- URL changes to `/chat?resume=<session_id>` and the page header/title updates.
- Main xterm area does not restore that session, or shows the previous fresh/live PTY.
- A separate read-only “Saved history” panel may hide the real issue while making the UI feel cluttered.

## Root cause

`/api/pty` honors the existing keep-alive PTY session for a matching `attach` token. If the same token is reused across fresh chat and resumed-session chat, the server reattaches to the existing PTY and the new `resume` target is effectively bypassed.

## Durable fix pattern

- Scope browser-side PTY attach-token storage by chat target, at minimum: selected profile + `resume` session id, with a separate `fresh` scope.
- Keep fresh-chat refresh resilience by continuing to reuse the `fresh` token for fresh chat.
- Rotate only the relevant scope when the user explicitly starts fresh.
- Avoid bolting on a separate “Saved history” transcript panel as the primary fix; old-session recovery should appear in the main xterm/TUI area.

## Verification

1. Build/typecheck the web bundle.
2. Open `/chat`, click a historical session in the right rail.
3. Assert no `[aria-label="Saved session history"]` panel exists if the panel was removed.
4. Assert `.xterm-screen` contains restored historical text.
5. Refresh the browser and assert the same resumed session and terminal text remain visible.

---
name: hermes-gateway-operations
description: Operate Hermes messaging gateway integrations, including platform setup, service persistence, message delivery checks, and dashboard media-handling pitfalls.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, gateway, messaging, weixin, dashboard, systemd]
    created_by: agent
---

# Hermes Gateway Operations

Use this skill when configuring, troubleshooting, or verifying Hermes messaging gateway platforms. The official Hermes docs and bundled `hermes-agent` skill remain authoritative; this skill captures operator workflow lessons and platform-specific pitfalls discovered during real setup.

## Workflow

1. Load the bundled `hermes-agent` skill and check official docs/CLI help first for current commands.
2. Check whether the gateway is already running before changing service state:
   ```bash
   hermes gateway status
   ```
3. For platform setup, prefer the official wizard when interactive menus are usable:
   ```bash
   hermes gateway setup
   ```
4. For WSL/Linux persistence, install the gateway as a user service when systemd is available:
   ```bash
   hermes gateway install --force --start-now --start-on-login
   ```
   Then verify both service and platform logs.
5. Verify the platform actually connected, not just that the service is active:
   ```bash
   tail -80 ~/.hermes/logs/gateway.log
   journalctl --user -u hermes-gateway -n 80 --no-pager
   ```
6. When testing outbound delivery, use the platform's expected channel semantics. A running gateway does not guarantee arbitrary proactive sends are accepted by the provider.

## Weixin / WeChat Notes

- Personal Weixin setup uses the `gateway.platforms.weixin` adapter and iLink QR login. The login stores `WEIXIN_ACCOUNT_ID`, `WEIXIN_TOKEN`, and related values in `~/.hermes/.env`.
- Required runtime imports for Weixin are `aiohttp` and `cryptography`; `qrcode[pil]` is useful for rendering QR images.
- The interactive platform menu may be awkward to automate in a pseudo-terminal. If the menu selection is unreliable, call `gateway.platforms.weixin.qr_login()` from Hermes' venv and write the returned credentials into `.env` deliberately.
- Set conservative defaults after QR login unless the user asks otherwise:
  ```env
  WEIXIN_DM_POLICY=pairing
  WEIXIN_ALLOW_ALL_USERS=false
  WEIXIN_GROUP_POLICY=disabled
  ```
- Weixin proactive sends may fail with iLink `sendmessage rate limited` even when credentials and gateway are valid. The reliable path is often: user sends a message to the bot first, gateway receives it, the adapter stores the peer `context_token`, and then Hermes replies in that context.
- `hermes send --list weixin` can show no targets until channel discovery has populated the channel directory. Do not treat an empty target list as proof the Weixin gateway is disconnected.

## Dashboard Media Pitfalls

- Hermes Dashboard can render embedded `data:image/...;base64,...` strings through its embedded-image extractor, but very long single-line data URIs can be brittle in conversation delivery.
- Prefer `MEDIA:/absolute/path/to/file.png` for attachments when the surface supports media delivery. If direct inline rendering is required and the image is small, data URI may work, but verify in the actual surface.
- For QR workflows, avoid spending the short QR validity window debugging display format. Generate a PNG and provide both a scannable attachment and the raw QR URL.

## References

- `references/weixin-dashboard-setup.md` contains a compact transcript-derived recipe for Weixin QR login, persistence, and delivery verification.

---
name: hermes-gateway-setup
description: Set up and troubleshoot Hermes messaging gateway platforms, with practical workflows for QR-login platforms, service persistence, and Dashboard media handoff.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, gateway, messaging, weixin, wechat, dashboard, systemd, wsl]
    related_skills: [hermes-agent]
---

# Hermes Gateway Setup

Use this skill when configuring Hermes Agent messaging platforms (`hermes gateway setup`, `hermes gateway run/install/status`) or troubleshooting gateway platform onboarding. Load `hermes-agent` first for the authoritative command reference, but use this skill for the pragmatic setup sequence and pitfalls discovered in real sessions.

## Default Workflow

1. Verify the Hermes install and config paths:
   ```bash
   which hermes
   hermes --version
   hermes config path
   hermes config env-path
   ```

2. Check whether the gateway is already running:
   ```bash
   hermes gateway status
   ```

3. Configure the platform with the official wizard when it is reliable:
   ```bash
   hermes gateway setup
   ```

4. Start manually for first verification:
   ```bash
   hermes gateway run
   ```

5. Confirm platform connection in logs:
   ```bash
   tail -80 ~/.hermes/logs/gateway.log
   ```

6. After the platform is confirmed, install as a user service when systemd is available:
   ```bash
   hermes gateway install --force --start-now --start-on-login
   hermes gateway status
   systemctl --user status hermes-gateway --no-pager
   ```

## WSL Persistence

WSL can run systemd user services when PID 1 is `systemd`. Check first:

```bash
ps -p 1 -o comm=
loginctl show-user "$USER" -p Linger 2>/dev/null || true
```

If systemd is available, `hermes gateway install --start-now --start-on-login` can enable linger and keep the gateway running after terminal logout. Be explicit with the user: a Windows reboot still requires WSL to be started by some process before the service can run.

If systemd is unavailable or unreliable, use tmux:

```bash
tmux new -s hermes-gateway 'hermes gateway run'
```

## Weixin / WeChat Personal Account Setup

For personal Weixin, Hermes stores these important variables in `~/.hermes/.env`:

```env
WEIXIN_ACCOUNT_ID=...
WEIXIN_TOKEN=...
WEIXIN_BASE_URL=https://ilinkai.weixin.qq.com
WEIXIN_CDN_BASE_URL=https://novac2c.cdn.weixin.qq.com/c2c
WEIXIN_DM_POLICY=pairing
WEIXIN_ALLOW_ALL_USERS=false
WEIXIN_ALLOWED_USERS=
WEIXIN_GROUP_POLICY=disabled
WEIXIN_GROUP_ALLOWED_USERS=
WEIXIN_HOME_CHANNEL=...
```

Recommended defaults:

- Direct messages: `pairing`
- Group chats: `disabled`
- Do not choose open access unless the user explicitly wants broad access.

The Weixin identity is an iLink bot account such as `...@im.bot`, not a fully scriptable personal WeChat account. Ordinary WeChat group events may not be delivered even if group policy is enabled.

## QR Login Pitfall

`hermes gateway setup` uses an interactive platform menu. In PTY automation or constrained dashboard sessions, arrow-key selection can land on an adjacent platform. If the menu repeatedly opens the wrong platform, do not keep fighting the menu. Call the Weixin adapter's `qr_login()` directly, then write the returned credentials to `~/.hermes/.env`.

See `references/weixin-qr-login.md` for a known-good direct login script and verification commands.

## Weixin Pairing And Delivery Pitfalls

After QR login, a successful gateway connection does not guarantee proactive sends to `WEIXIN_HOME_CHANNEL` will work immediately. iLink may return `sendmessage rate limited`; ask the user to send a DM to the bot first so the gateway can store a peer `context_token`, then approve the user and retry.

`hermes pairing list` may display a short code that is only a hash prefix, not the original pairing code. If `hermes pairing approve weixin <displayed-code>` fails even though the pending row is visible, use the PairingStore workaround only after the operator explicitly identifies the user to approve.

See `references/weixin-pairing-and-send.md` for the context-token check, manual approval workaround, and direct `send_weixin_direct()` probe.

## Dashboard QR / Media Handoff

Hermes Dashboard can render embedded `data:image/png;base64,...` images via its embedded-image extraction path, but very long single-line data URIs can be brittle in chat responses. For QR codes, prefer:

1. Generate a PNG file and send it as a media attachment/path appropriate for the active surface.
2. Include the QR URL as a text fallback.
3. Use data URI only when the surface demonstrably renders it and the payload is reasonably small.

Avoid letting the QR login timeout while experimenting with presentation. Generate the QR, immediately hand it to the user, and poll the login process.

## Verification Checklist

After successful login or service setup, verify all of these before declaring done:

```bash
hermes gateway status
systemctl --user status hermes-gateway --no-pager  # if installed as service
tail -80 ~/.hermes/logs/gateway.log
```

Expected Weixin log lines:

```text
Connecting to weixin...
[Weixin] Connected account=... base=https://ilinkai.weixin.qq.com
✓ weixin connected
Gateway running with 1 platform(s)
```

## User Experience Notes

When the user is waiting to scan a QR code, keep the loop tight: generate a fresh code, present it clearly, then immediately poll for completion. If a prior response broke due to media formatting, switch format quickly instead of explaining at length.

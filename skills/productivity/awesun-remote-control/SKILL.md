---
name: awesun-remote-control
description: Use when the user asks to manage or remotely control devices through the 向日葵/AweSun MCP service, including device search, remote desktop, screenshots, commands, keyboard/mouse actions, wake, shutdown, port forwarding, and session cleanup. Includes WSL/Windows-aware setup and diagnostics.
version: 1.1.0
license: LicenseRef-Upstream-Unspecified
metadata:
  hermes:
    tags: [awesun, remote-control, mcp, windows, wsl]
    related_skills: [computer-use]
---

# AweSun Remote Control for Hermes

## Overview

This is a Hermes-compatible adaptation of `OrayDev/awesun-skill`. It invokes the MCP server bundled with AweSun 16.3.2+ through `executor.py`. It fixes the upstream executor's undefined-variable bug, preserves the process environment, supports WSL/Windows paths, avoids storing tokens in the skill, and adds bounded diagnostics.

Remote actions affect another computer. Follow the user's requested scope exactly. Never enter passwords, tokens, payment data, or other secrets. Require explicit confirmation immediately before shutdown, wake, device removal, or other disruptive actions.

## When to Use

Use for:
- finding and inspecting AweSun devices;
- opening/closing desktop, CMD, SSH, file, camera, or forwarding sessions;
- screenshots and user-requested keyboard/mouse operations;
- user-requested remote commands;
- diagnosing AweSun MCP setup.

Do not use this skill for the local Hermes desktop; use `computer-use` instead.

## Prerequisites

1. Windows/macOS must have AweSun 16.3.2+ installed, running, and logged in.
2. AweSun MCP must be enabled in **stdio** mode.
3. Obtain the command and `AWESUN_API_TOKEN` from AweSun's “其他（通用配置）” screen. Do not ask the user to paste the token into chat.
4. In the current shell, set the token privately:

```bash
export AWESUN_API_TOKEN='value copied locally by the user'
```

Optional overrides:

```bash
export AWESUN_MCP_COMMAND='C:\Program Files\Oray\Awesun\awesun-mcp-server.exe'
export AWESUN_API_URL='http://127.0.0.1:8908'
```

The executor auto-converts a Windows drive path to `/mnt/<drive>/...` under WSL and checks common install locations.

## Workflow

Run from the skill directory shown by `skill_view` or use the absolute path:

```bash
cd ~/.hermes/skills/productivity/awesun-remote-control
python3 executor.py --check
python3 executor.py --list
python3 executor.py --describe device_search
```

Standard call flow:

1. Run `--check`; continue only when command, token, Python MCP package, and API endpoint checks pass.
2. Use `--list` or `--describe TOOL` rather than relying on stale schemas.
3. For device operations, call `device_search` first and use the returned `remote_id`.
4. Establish the correct session type with `control_connect` and retain its `session_id`.
5. Call the requested tool using JSON:

```bash
python3 executor.py --call '{"tool":"control_sessions","arguments":{}}'
```

6. Verify the result through a read-only call or screenshot.
7. Call `control_disconnect` when finished. Completion means no unneeded session remains active.

## Safety Rules

- Treat `AWESUN_API_TOKEN` as a secret; keep it in an environment variable, never in `SKILL.md`, `mcp-config.json`, logs, or chat.
- Before `device_shutdown`, `device_wakeup`, or `device_remove`, state the target device and ask for explicit confirmation.
- Before a remote command, show the exact command unless it is a harmless read-only inspection directly requested by the user.
- Never disable remote-host security controls or bypass login/UAC prompts.
- After each state-changing GUI action, request a screenshot and verify the intended state.
- On failure, stop repeated clicking/typing and diagnose first.

## Common Tools

- Devices: `device_search`, `device_info`, `device_add`, `device_update`, `device_remove`, `device_wakeup`, `device_shutdown`
- Sessions: `control_connect`, `control_sessions`, `control_disconnect`, `control_screenshot`, `control_command`, `control_portforward`
- Desktop: `desktop_click_mouse`, `desktop_drag_mouse`, `desktop_move_mouse`, `desktop_scroll_mouse`, `desktop_typing_text`, `desktop_typing_keys`, `desktop_press_keys`, `desktop_paste_text`, `desktop_waiting`

Coordinates are normalized values from 0.0 to 1.0. Calculate them from screenshot pixel coordinates and dimensions; do not guess when precision matters.

## Troubleshooting

- `AweSun MCP command not found`: install/update AweSun, enable MCP stdio mode, then set `AWESUN_MCP_COMMAND` from the generated config.
- `AWESUN_API_TOKEN is not set`: export it locally in the shell; do not write it into the skill.
- `connection refused` on port 8908: start AweSun and enable its MCP service.
- `mcp package is not installed`: run the executor with Hermes' Python or install `mcp` in an isolated environment.
- Timeout: verify AweSun is running and the configured command actually starts a stdio MCP server.

## Verification Checklist

- [ ] `python3 executor.py --check` reports `ready: true`
- [ ] `python3 executor.py --list` returns MCP tools
- [ ] `--describe device_search` returns an input schema
- [ ] A read-only `device_search` succeeds
- [ ] Any created session is disconnected after the task

---
name: codex-wsl-interop
description: Use and troubleshoot Codex CLI from Hermes running in WSL when the user's working Codex setup is on Windows or uses a custom provider.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [wsl, windows]
metadata:
  hermes:
    tags: [codex, wsl, windows, troubleshooting, delegation]
    related_skills: [codex]
    created_by: agent
---

# Codex WSL Interop

Use this skill when Hermes is running inside WSL and the user asks Hermes to delegate work to Codex, especially when Codex works for the user on Windows but fails from Hermes/WSL.

## Workflow

1. Confirm which Codex binary Hermes is using:

```bash
command -v codex
codex --version
```

2. Compare WSL and Windows Codex configuration before assuming Codex itself is broken:

```bash
sed -n '1,120p' ~/.codex/config.toml
sed -n '1,120p' /mnt/c/Users/<WindowsUser>/.codex/config.toml
```

3. If Windows Codex uses a custom provider, copy only WSL-compatible provider/model settings into `~/.codex/config.toml`. Do not blindly copy Windows-only `notify`, `mcp_servers`, `desktop`, or `[windows]` sections.

4. If WSL Codex reaches the provider but returns `401 API_KEY_REQUIRED`, copy the Windows Codex auth file and restrict permissions:

```bash
cp /mnt/c/Users/<WindowsUser>/.codex/auth.json ~/.codex/auth.json
chmod 600 ~/.codex/auth.json
```

5. Verify with a minimal task before launching a long coding job:

```bash
codex exec "Reply with OK only"
```

Only after that succeeds should Hermes send Codex a real implementation task.

## Known Good Minimal Config Shape

```toml
model_provider = "OpenAI"
model = "gpt-5.5"
review_model = "gpt-5.5"
model_reasoning_effort = "xhigh"
disable_response_storage = true
network_access = "enabled"
windows_wsl_setup_acknowledged = true

[model_providers.OpenAI]
name = "OpenAI"
base_url = "https://ai.gs88.shop"
wire_api = "responses"
requires_openai_auth = true

[features]
goals = true

[projects."/home/wzk/.hermes/hermes-agent"]
trust_level = "trusted"
```

Adjust the project path and provider values to the user's environment.

## Running Windows Codex From WSL

Calling the Windows npm wrapper directly from WSL can fail because it may try to load Linux optional dependencies. If you must run Windows Codex, invoke it through Windows shell:

```bash
powershell.exe -NoProfile -Command "Set-Location 'C:\\Users\\<WindowsUser>\\some-windows-git-repo'; codex.cmd exec --skip-git-repo-check 'Create file codex-ok.txt containing ok'"
```

Caveats:

- Windows Codex may not operate correctly with WSL UNC paths as its working directory. Prefer a Windows-local git repo/temp copy, then sync the result back to WSL.
- Shell commands inside the Windows Codex sandbox can fail with `CreateProcessAsUserW failed: 5`; file edits through Codex apply-patch may still work.

## Pitfalls

- Do not treat `codex --version` succeeding as proof that `codex exec` can reach the configured model provider.
- Do not trust Codex exit code alone. Verify real success by checking for Codex's final summary, changed files, and targeted tests.
- If Codex prints repeated reconnects/timeouts, check provider config and auth before repeatedly changing the task prompt.

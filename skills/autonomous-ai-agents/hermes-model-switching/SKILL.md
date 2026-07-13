---
name: hermes-model-switching
description: Safely switch Hermes Agent model, provider, API endpoint, or API keys with backup, validation, and rollback steps.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, configuration, model, provider, api-key, rollback]
---

# Hermes Model Switching

Use this skill when the user wants to change Hermes Agent's model, provider, API endpoint, API key, fallback providers, or related inference configuration.

## Current Known Backup

A known-good backup for the default profile exists at:

```text
/home/wzk/.hermes/backups/config-20260703-134020
```

It contains:

```text
/home/wzk/.hermes/backups/config-20260703-134020/config.yaml
/home/wzk/.hermes/backups/config-20260703-134020/.env
```

Use this only when working on the default profile unless the user explicitly says another profile is involved.

## Safety Rules

1. Load the `hermes-agent` skill first if not already loaded.
2. Treat official docs as authoritative when command behavior is uncertain: https://hermes-agent.nousresearch.com/docs
3. Before changing config, inspect the active profile and config paths:

```bash
hermes config path
hermes config env-path
hermes config
```

4. Create a fresh timestamped backup before every model/API change, even if the known backup exists:

```bash
stamp=$(date +%Y%m%d-%H%M%S)
backup_dir="$HOME/.hermes/backups/config-$stamp"
mkdir -p "$backup_dir"
cp -a "$HOME/.hermes/config.yaml" "$backup_dir/config.yaml"
[ -f "$HOME/.hermes/.env" ] && cp -a "$HOME/.hermes/.env" "$backup_dir/.env"
printf 'Backed up to: %s\n' "$backup_dir"
stat -c '%a %U:%G %n' "$backup_dir" "$backup_dir/config.yaml" "$backup_dir/.env" 2>/dev/null || true
```

5. Never print API keys or secrets. If `.env` must be inspected, search for variable names only or use redacted output.
6. Do not modify another profile under `~/.hermes/profiles/<name>/` unless the user explicitly asks.

## Preferred Switching Paths

### Interactive Model Picker

Use when the user is present and wants to choose from available providers/models:

```bash
hermes model
```

### Direct Config Change

Use when the user states the exact provider/model:

```bash
hermes config set model.provider <provider>
hermes config set model.default <model>
```

Examples:

```bash
hermes config set model.provider openrouter
hermes config set model.default anthropic/claude-sonnet-4.6
```

For custom endpoints, set the endpoint and model according to the current Hermes docs and existing config shape. Common keys are:

```bash
hermes config set model.provider custom
hermes config set model.base_url <base_url>
hermes config set model.default <model_name>
```

### API Keys

Prefer Hermes auth flows where available:

```bash
hermes auth
hermes auth add <provider>
hermes auth list <provider>
```

For env-var based providers, update `~/.hermes/.env` carefully. Do not echo secrets into chat output.

## Verification

After switching, run:

```bash
hermes config check
hermes doctor
hermes chat -q 'Reply with the active model and provider if visible, then say OK.'
```

If one-shot mode is available and desired, this is also acceptable:

```bash
hermes -z 'Reply with OK.'
```

If config changes do not affect the current session, tell the user to restart Hermes or start a new session. Config is read at startup for many settings.

## Rollback

If the new model/API setup fails and the user wants to restore the known backup for the default profile:

```bash
cp -a /home/wzk/.hermes/backups/config-20260703-134020/config.yaml /home/wzk/.hermes/config.yaml
cp -a /home/wzk/.hermes/backups/config-20260703-134020/.env /home/wzk/.hermes/.env
hermes config check
```

For a fresher backup made during the same task, prefer rolling back to that fresher backup instead of the known backup above.

## Notes

- `--yolo` or `/yolo` may be needed in CLI sessions where command approvals do not render visibly.
- `approvals.mode off` disables approval prompts persistently; `approvals.mode smart` is a safer middle ground.
- Secret redaction is separate from approvals and should generally stay enabled.

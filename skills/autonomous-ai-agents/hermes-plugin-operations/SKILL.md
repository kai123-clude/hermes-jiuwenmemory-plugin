---
name: hermes-plugin-operations
description: Install, enable, and verify Hermes Agent plugins, including pip-distributed entry points and plugins that depend on external CLI binaries.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows, wsl]
metadata:
  hermes:
    tags: [hermes, plugins, configuration, setup, verification]
    related_skills: [hermes-agent, hermes-skill-operations]
---

# Hermes Plugin Operations

Use this skill when the user asks to install, enable, disable, inspect, or troubleshoot a Hermes plugin. This covers local plugins, pip-distributed plugins, and plugins that register through Python entry points such as `hermes_agent.plugins`.

## Workflow

1. Identify the plugin type and expected activation name.
   - For pip packages, inspect `pyproject.toml` or package metadata for `[project.entry-points."hermes_agent.plugins"]`.
   - The config name is the entry-point name, not necessarily the package or import module name.

2. Check installation in the same Python environment that runs Hermes.
   - Prefer Hermes' venv when present: `$HOME/.hermes/hermes-agent/venv/bin/python`.
   - Verify import and distribution metadata with `importlib.util.find_spec()` and `importlib.metadata.distribution()`.
   - Do not treat installation into system Python, conda, or a random venv as sufficient for Hermes.

3. Check external runtime dependencies separately.
   - Some plugins only register or work when a companion binary exists on `PATH`.
   - Verify the companion CLI with `command -v <binary>`, `<binary> --version`, and one minimal functional command from the plugin README.
   - If the dependency is missing, capture the fix as an install/config step, not as a durable claim that the plugin is broken.

4. Back up Hermes config before editing.
   - Copy `~/.hermes/config.yaml` to a timestamped directory under `~/.hermes/backups/`.
   - Report the backup path in the final answer.

5. Enable the plugin in `~/.hermes/config.yaml`.
   - For Hermes versions where `hermes plugins enable <name>` does not recognize pip-only entry points, update YAML directly.
   - Add only the needed entry under `plugins.enabled`; preserve existing enabled plugins.

   ```yaml
   plugins:
     enabled:
       - plugin-entry-point-name
   ```

6. Verify after changes.
   - Confirm `plugins.enabled` contains the entry-point name when the plugin is enabled through the plugin loader. Memory provider plugins may instead activate through `memory.provider`; do not require them to appear in `plugins.enabled` unless their README says so.
   - Confirm the entry point exists in Hermes' Python environment:

   ```bash
   "$HOME/.hermes/hermes-agent/venv/bin/python" - <<'PY'
   from importlib.metadata import entry_points
   for ep in entry_points(group='hermes_agent.plugins'):
       print(f'{ep.name} = {ep.value}')
   PY
   ```

   - For memory provider plugins, distinguish three levels: Hermes provider switch, plugin/API health, and functional memory search/write. A healthy `/health` response is not enough; run the provider's status/search/store tools or instantiate the provider from source to verify recall and writes.
   - Confirm required companion binaries are available and functional.
   - Tell the user a Hermes restart or new session is required for config/plugin changes to load.

## JiuwenMemory memory providers

For JiuwenMemory provider work, use `references/jiuwenmemory.md` for the diagnostic checklist and `references/jiuwenmemory-local-bge-m3.md` for the local ModelScope/FlagEmbedding deployment pattern. When the user asks whether article-level AutoGenetic Memory features are implemented, use `references/jiuwenmemory-autogenetic-gaps.md` for the implementation and verification checklist (session_id forwarding, Dreaming endpoints, L2 semantic/episodic tests, Graph/Swarm/MemoryTurbo boundaries, and a known-good Phase A L2/Dreaming verification probe). For the user's preferred phased implementation workflow and known-good Phase A/B/C1/C2/C3 verification probes, approval-gated restart/script pitfalls, benchmark/token-reduction harness shape, and benchmark-script verification discipline, use `references/jiuwenmemory-phase-workflows.md`. When migrating a rejected in-tree memory-provider PR to the upstream-approved standalone form, use `references/standalone-memory-provider-migration.md`.

Important boundary: Hermes can enable the provider and expose tools, but native layered memory/search depends on the JiuwenMemory server's own embedding configuration (`~/.jiuwenmemory/.env`, especially `EMBED_MODEL_NAME`, `EMBED_API_KEY`, `EMBED_API_BASE`). A healthy `/health` check is insufficient; verify `jiuwenmemory_status` and/or a direct embeddings probe. If native search fails, a Hermes-side fallback journal can prevent memory loss, but it is not a replacement for JiuwenMemory's L0-L3 layered memory.

User workflow preference for this class of work: Hermes should act as orchestrator/planner/verifier while Codex performs code edits for Hermes/JiuwenMemory plugin or server implementation. If the user says code writing should be left to Codex, stop hand-editing feature code; poll/wait for Codex, then independently run tests and end-to-end verification. Be precise about process state: do not say work is stopped/paused when Codex is still running.

## Example: pip plugin with an external CLI

For a package like `rtk-hermes`:

- Python distribution: `rtk-hermes`
- Import module: `rtk_hermes`
- Hermes plugin entry point: `rtk-rewrite`
- Companion CLI: `rtk`

The plugin can be installed and configured correctly while still doing nothing at runtime if `rtk` is absent. Verify both layers before declaring it fully active.

## Pitfalls

- When an in-tree memory-provider PR is rejected under the no-new-in-tree-provider policy, migrate it to a standalone repo whose root itself is the provider directory (`__init__.py` + `plugin.yaml`), so users can `git clone <repo> ~/.hermes/plugins/<provider>` or symlink it there. Keep tests that verify discovery through `$HERMES_HOME/plugins/<provider>` against a Hermes main checkout that does not contain the provider in-tree; otherwise bundled-provider precedence can mask a broken standalone install.
- Running provider diagnostics from a symlinked plugin repo can create runtime log/output directories in the repo depending on the active Hermes logging config. Add `logs/`, benchmark outputs, caches, and build artifacts to `.gitignore` before committing.
- Do not confuse `git clone` with installation. A cloned repo proves source is present; it does not prove the plugin is installed into Hermes' runtime.
- Do not assume `hermes plugins enable` works for all pip-distributed entry points. If the plugin README warns about this, edit `plugins.enabled` directly.
- For memory provider plugins, do not stop at `plugins/memory/<name>/`. If the provider exposes a primary credential env var, add it to `OPTIONAL_ENV_VARS` in `hermes_cli/config.py` with `category: "tool"`, `password: true`, and the provider's primary search/recall tool in `tools`; update `tests/hermes_cli/test_config.py::TestMemoryProviderEnvVarsRegistry` when that map exists.
- For memory provider plugins backed by a separate server, expose diagnostic status that goes beyond `/health`. Probe the actual recall/search path and surface actionable backend knobs (for example embedding model/base/key settings) when search or writes fail while health is green.
- Respect the user's requested boundary: if they ask for a Hermes plugin integration, do not deploy or take ownership of the backing memory service unless they explicitly ask. Make the plugin expose required server-side env/config (`EMBED_MODEL_NAME`, `EMBED_API_KEY`, `EMBED_API_BASE`, etc.) and clear diagnostics instead.
- When a memory server's native vector search/write is blocked by an external embedding backend, a Hermes-side fallback can preserve usability: write failed memories to a local JSONL journal under `$HERMES_HOME`, expose `backup_paths()`, and use bounded lexical recall as a degraded mode. Label results as fallback/degraded and continue to recommend proper server embedding config for full native recall.
- When the upstream memory API is not fully known, prefer a conservative REST adapter with endpoint paths configurable from `$HERMES_HOME/<provider>.json`; document the expected default request/response shapes in the plugin README so route changes do not require code edits.
- Memory provider `sync_turn()` and `on_memory_write()` hooks must be non-blocking; capture API writes in background threads or queues and add focused tests that prove the public hook returns quickly. Also test degraded/fallback write and search paths using fake clients that raise embedding failures and timeouts.
- Avoid adding environment-specific failures to persistent notes. Record the durable recovery path: install into Hermes' venv, enable entry point in config, install required companion CLI, then restart Hermes.
- Config changes do not affect the already-running session. Make this explicit when reporting success.

# Standalone memory-provider migration

Use this when an upstream Hermes PR adding `plugins/memory/<provider>/` is closed under the no-new-in-tree-memory-provider policy.

## Goal

Convert the provider into a repo that can be installed as a user memory plugin without touching Hermes core:

```bash
git clone <repo-url> ~/.hermes/plugins/<provider>
# or symlink a local checkout:
ln -sfn /path/to/<provider-repo> ~/.hermes/plugins/<provider>
```

The standalone repo root should itself look like the provider directory:

```text
<provider-repo>/
  __init__.py        # implements MemoryProvider or register(ctx)
  plugin.yaml
  README.md
  tests/
  scripts/           # optional operational probes/benchmarks
```

This works because Hermes scans `$HERMES_HOME/plugins/<name>/` and treats each matching directory as a user-installed memory provider.

## Migration checklist

1. Copy the provider directory contents to the new repo root, not to `plugins/memory/<name>/` inside the repo.
2. Copy useful provider-specific scripts/docs, but keep generated reports out of git.
3. Add an install helper that symlinks the repo to `$HERMES_HOME/plugins/<name>`.
4. Add README instructions to set:

   ```yaml
   memory:
     provider: <name>
   ```

5. Adapt tests so they import the standalone root module by path, while adding a Hermes checkout to `sys.path` for `agent.memory_provider`, `tools.registry`, and discovery imports.
6. Add a discovery test that creates a temporary `$HERMES_HOME/plugins/<name>` symlink to the repo and asserts `discover_memory_providers()` and `load_memory_provider(<name>)` find it.
7. Run tests twice:
   - against the current Hermes checkout;
   - against a clean Hermes main checkout/worktree that does **not** contain the provider in-tree, to avoid bundled-provider precedence masking a bad standalone layout.
8. Add `logs/`, benchmark outputs, caches, build artifacts, and egg-info to `.gitignore` before committing. Provider status probes can create log directories inside the symlinked repo depending on active Hermes logging config.

## Verification pattern

```bash
cd /path/to/<provider-repo>
python -m pytest -q
HERMES_AGENT_REPO=/tmp/hermes-agent-main python -m pytest -q
./install.sh
PYTHONPATH=/tmp/hermes-agent-main python - <<'PY'
from plugins.memory import discover_memory_providers, find_provider_dir, load_memory_provider
name = '<provider>'
providers = {n: (desc, available) for n, desc, available in discover_memory_providers()}
assert name in providers
provider = load_memory_provider(name)
assert provider is not None
print(find_provider_dir(name), provider.name, provider.is_available())
PY
```

For JiuwenMemory specifically, also run `jiuwenmemory_status` or instantiate the provider and call its status tool. A healthy server should report both `/health` success and `memory_search: ok`; `/health` alone is not sufficient.
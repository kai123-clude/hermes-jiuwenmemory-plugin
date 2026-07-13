# Hermes Skills Snapshot

This repository includes a snapshot of the user-local Hermes skills under [`skills/`](skills/).

## Scope

The snapshot contains every directory under `~/.hermes/skills/` that has a `SKILL.md`, including its reusable `scripts/`, `references/`, `templates/`, and `assets/` files.

The following runtime-only content is intentionally excluded:

- `.venv/` and `venv/`
- `.hub/` indexes
- `.curator_backups/`
- `__pycache__/` and `.pytest_cache/`
- generated `work/`, `dist/`, and `build/` directories
- `node_modules/`
- local credentials and environment files

No API keys, tokens, passwords, private keys, browser cookies, or Hermes memory databases should be committed. Run a secret scan before every push.

## Refresh

From the repository root:

```bash
python3 scripts/sync_hermes_skills.py --prune
```

The command rewrites each synchronized skill directory and generates [`skills/MANIFEST.json`](skills/MANIFEST.json) with file hashes and counts.

## Restore on another machine

Review the snapshot first, then copy only the skills you need:

```bash
cp -a skills/<category>/<skill-name> "$HOME/.hermes/skills/<category>/"
```

Do not copy `skills/MANIFEST.json` into the Hermes skills directory. Skills with Python or system dependencies may require their documented setup steps after restoration.

## Provenance and licensing

The snapshot contains a mixture of locally authored, adapted, and upstream-provided skills. Each skill retains its own source and license metadata where available. Inclusion in this repository does not relicense third-party content. In particular, `skill-omni-creation` records its upstream openJiuwen provenance and redistribution caveat in its own documentation.

---
name: reproducible-local-ai-deployment
description: "Package a live local/WSL AI stack into a safe, reproducible deployment repository with version tracking, model manifests, service templates, and encrypted private-state migration."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [reproducibility, deployment, wsl, model-manifest, backup, privacy]
    created_by: agent
---

# Reproducible Local AI Deployment

Use when a user wants to move a working local AI stack to another machine, upload “all source/models/environment/memory” to GitHub, or continuously track a deployed stack.

The deliverable is a **reproducible deployment repository**, not a raw copy of the home directory.

## Core separation

Classify every artifact before writing or uploading:

1. **Git-tracked control plane**
   - Deployment scripts, sanitized configuration templates, service definitions, source remotes and commit pins, package/runtime manifests, model identifiers/revisions/checksums, verification scripts, and migration documentation.
2. **Re-downloadable heavy artifacts**
   - Model weights, package caches, virtual environments, `node_modules`, containers, and generated build outputs. Track download/build recipes and integrity metadata instead of binaries.
3. **Private runtime state**
   - Memories, session stores, databases, logs, profiles, OAuth state, API keys, auth files, and personal configuration. Never place these in ordinary Git history. Export through an explicit allowlist into an encrypted archive stored outside the repository.
4. **Independent source repositories**
   - Record remote URLs and immutable commits. Do not duplicate entire upstream histories unless the user explicitly needs a vendor mirror and licensing has been reviewed.

Default a repository containing deployment metadata to **private**, but still treat it as potentially exposed. Private visibility is not a substitute for secret hygiene.

## Workflow

1. **Read-only inventory**
   - Measure major directory sizes and identify source repos, services, model locations, environments, databases, and configuration roots.
   - Inspect secret *variable names* when needed, never print values.
   - Record live health separately from filesystem presence.

2. **Choose the migration boundary**
   - Explain why venvs are rebuilt, models are downloaded, source repos are pinned, and private state is encrypted.
   - Keep credentials local to each destination machine.

3. **Build the repository**
   Include at minimum:
   - A comprehensive `.gitignore`.
   - Chinese or user-requested-language README with install, restore, verify, and update flows.
   - Sanitized `.env.example`/configuration templates.
   - Idempotent install/bootstrap script using `$HOME`, never a specific username.
   - Model download script with repository ID, revision, target path, and optional checksum verification.
   - systemd user-unit templates using `%h` where supported.
   - Source/version manifest generator.
   - Health verification script.
   - Encrypted private-state export/import scripts with explicit allowlists.
   - CI checks for shell syntax and likely committed secrets.

4. **Verify before commit**
   - Run shell syntax checks.
   - Exercise install scripts in `--dry-run` mode.
   - Run health verification against the live deployment.
   - Run a secret scanner or focused regex scan over candidate tracked files.
   - Run `git diff --check`.
   - For any changed behavior lacking a canonical suite, create a temporary `/tmp/hermes-verify-*` script, test the exact behavior, remove it, and report this as **ad-hoc verification**, not “suite green.”

5. **Publish safely**
   - Commit only after verification.
   - Create/push to a private remote.
   - Read back remote visibility and tree after push when tooling permits.
   - Never report upload success without a verifiable URL/remote state.

6. **Track changes**
   - Provide a deterministic manifest-update command and a review-before-push workflow.
   - Prefer manual review or CI-triggered updates over blindly committing on a timer.
   - Changes to private memory belong in encrypted backups, not recurring Git commits.

## Important implementation details

- Export scripts should use a temporary directory, an explicit allowlist, `set -euo pipefail`, restrictive output permissions, and encryption before durable output is created.
- Import scripts should validate archive existence and structure, avoid path traversal, and advise stopping/restarting services around database restoration.
- A generated manifest must create its parent directory itself; test from a missing-directory state.
- A “working local environment” can be many gigabytes while the deployment repo remains small. This is expected and desirable.
- If a coding delegate fails because of transient setup state, continue directly or repair setup; do not let delegation block the deliverable.

## Pitfalls

- Uploading a private repository with secrets because “private means safe.”
- Committing model weights without an explicit Git LFS/release-storage decision.
- Copying virtual environments across machines instead of rebuilding from locks.
- Treating service health as proof that migration scripts work.
- Claiming full verification after only checking one script.
- Stopping after scaffolding; exercise the generated artifacts against the live system.

## References

- `references/hermes-jiuwenmemory-wsl.md` — concrete artifact boundaries and checks for a Hermes + JiuwenMemory + local embedding stack.

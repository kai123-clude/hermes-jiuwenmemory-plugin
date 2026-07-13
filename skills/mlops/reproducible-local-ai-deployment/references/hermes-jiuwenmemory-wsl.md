# Hermes + JiuwenMemory on WSL: deployment-repository notes

Use this reference when packaging a stack containing Hermes Agent, a standalone JiuwenMemory `MemoryProvider`, JiuwenMemory Server, and a local OpenAI-compatible BGE-M3 embedding service.

## Recommended tracked artifacts

- Hermes fork/upstream remote URLs and exact commits.
- Standalone plugin remote URL and exact commit.
- Hermes CLI/Python versions.
- Model identifier such as `BAAI/bge-m3`, revision, expected target path, and optional file checksums.
- Sanitized Hermes and JiuwenMemory environment templates.
- systemd user units for the embedding server and memory server.
- Install, model-download, manifest-update, health-check, and encrypted state-migration scripts.

## Keep outside Git

- `~/.hermes/.env`, `auth.json`, credential pools, SSH/GitHub credentials.
- Hermes `state.db`, session transcripts, logs, snapshots, fallback journals.
- JiuwenMemory `memory_data/`, graph/turbo/swarm SQLite stores, and server `.env`.
- BGE-M3 weights, embedding-server venv, Hermes venv, `node_modules`, caches.

## Runtime checks

Verify all of these independently:

1. Hermes CLI exists and reports a version.
2. Hermes and plugin source directories are Git repos at recorded commits.
3. Model directory has expected metadata (for example `config.json`).
4. Embedding systemd service is active.
5. JiuwenMemory systemd service is active.
6. Embedding `/v1/models` responds.
7. JiuwenMemory `/health` responds.
8. When available, perform a lightweight memory-search probe; health alone does not prove embeddings/search work.

## State migration

Use an explicit allowlist and symmetric GPG or age encryption. Store the output outside the repository with mode `0600`. Stop services before snapshotting/restoring databases when consistency matters. Do not include API credentials by default; provision them separately on the destination.

## Focused verification pattern

When a manifest generator is changed, test it from a deliberately absent output directory:

- remove only the generated `manifest/` in a disposable fixture or safe repo state;
- run the generator;
- assert expected source commit and model fields;
- scan generated output for credential-looking assignments;
- run `git diff --check`;
- label this evidence ad-hoc unless a canonical project suite also ran.

# JiuwenMemory local BGE-M3 embedding deployment

Use this when Hermes has `memory.provider: jiuwenmemory` and `hermes memory status` shows the provider active, but native memory search/write still fails because the JiuwenMemory server embedding backend is not working.

## Symptom pattern

- `jiuwenmemory_status` / `GET /health` returns healthy.
- `POST /search_memory/` fails with an error like `retrieval embedding_request call failed` or `Failed to get embedding after 3 attempts`.
- The configured chat gateway may support chat models but no embedding models; verify with `/models` and a direct `POST /embeddings` probe before blaming Hermes.

## Fast diagnosis

1. Inspect `~/.jiuwenmemory/.env` without printing secrets:
   - `MODEL_PROVIDER`, `MODEL_NAME`, `API_BASE`
   - `EMBED_MODEL_NAME`, `EMBED_API_BASE`, whether `EMBED_API_KEY` is set
2. Test the embedding endpoint directly with payload:
   ```json
   {"model":"<EMBED_MODEL_NAME>","input":"ping"}
   ```
3. If the endpoint returns `model_not_found` or no vector, the JiuwenMemory server cannot build native vector/layered memory even if `/health` is healthy.

## Local BGE-M3 deployment pattern

A working local setup can use ModelScope `BAAI/bge-m3` + FlagEmbedding behind a tiny OpenAI-compatible FastAPI service.

Recommended paths:

- Service root: `~/.jiuwenmemory/embedding-server/`
- Model cache: `~/.jiuwenmemory/models/BAAI/bge-m3`
- Embedding endpoint: `http://127.0.0.1:18080/v1/embeddings`

High-level steps:

1. Create an isolated venv under `~/.jiuwenmemory/embedding-server/`.
2. Install `fastapi`, `uvicorn[standard]`, `modelscope`, and `FlagEmbedding`. Use a regional PyPI mirror if PyPI times out.
3. Download `BAAI/bge-m3` with `modelscope.snapshot_download(..., cache_dir='~/.jiuwenmemory/models')`.
4. Implement `/v1/embeddings` returning OpenAI-style:
   ```json
   {"object":"list","data":[{"object":"embedding","index":0,"embedding":[...]}],"model":"BAAI/bge-m3"}
   ```
5. Force CPU in WSL if CUDA drivers are mismatched: `CUDA_VISIBLE_DEVICES=''`.
6. Set `~/.jiuwenmemory/.env`:
   ```env
   EMBED_MODEL_NAME=BAAI/bge-m3
   EMBED_API_BASE=http://127.0.0.1:18080/v1/embeddings
   EMBED_API_KEY=
   ```
7. Restart the JiuwenMemory server after changing `.env`.

## Durable service pattern

When systemd user services are available (`systemctl --user is-system-running`) and linger is enabled, create two user services:

- `jiuwen-bge-m3-embedding.service`: runs `uvicorn server:app --host 127.0.0.1 --port 18080` from the embedding server directory.
- `jiuwen-memory-server.service`: runs Hermes' `memory-server` and `Requires=/After=` the embedding service.

Enable and start both:

```bash
systemctl --user daemon-reload
systemctl --user enable jiuwen-bge-m3-embedding.service jiuwen-memory-server.service
systemctl --user start jiuwen-bge-m3-embedding.service jiuwen-memory-server.service
```

## Verification

- Direct embedding probe returns a vector; BGE-M3 dense vectors are 1024-dimensional.
- `jiuwenmemory_status` returns `memory_search: ok`.
- `POST /add_messages/` returns success.
- `search_memory` can return typed memories such as `user_profile`.
- `search_user_history_summary` can return `summary` records.

Layer generation depends on content: preferences commonly become `user_profile` plus `summary`; `semantic_memory` and `episodic_memory` may remain empty for simple preference tests.
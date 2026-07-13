# JiuwenMemory memory-provider diagnostics

Use this when a Hermes session has `memory.provider: jiuwenmemory` and `hermes memory status` reports the provider installed/active, but real memory search or writes do not work.

## Key distinction

Hermes' JiuwenMemory plugin is only the provider bridge. The JiuwenMemory memory-server does the actual LLM extraction, embeddings, vector search, and layered memory. A healthy `/health` response does **not** prove native memory search/write works.

Check both layers:

1. Hermes provider activation:
   ```bash
   hermes memory status
   python3 - <<'PY'
   import yaml
   from pathlib import Path
   cfg=yaml.safe_load(Path('~/.hermes/config.yaml').expanduser().read_text()) or {}
   print(cfg.get('memory'))
   PY
   ```
2. Provider runtime diagnostic:
   ```text
   jiuwenmemory_status
   ```
   Healthy bridge but broken native search commonly appears as:
   ```json
   {
     "status": "healthy",
     "memory_search": "failed",
     "memory_search_error": "... Failed to get embedding after 3 attempts ..."
   }
   ```

## Embedding configuration is server-side

The server reads its own env, usually `~/.jiuwenmemory/.env`; this is separate from Hermes `~/.hermes/config.yaml`.

Common variables:

```env
MODEL_PROVIDER=OpenAI
MODEL_NAME=<chat-model>
API_BASE=<openai-compatible-v1-base>
API_KEY=<chat-key>

EMBED_MODEL_NAME=<embedding-model>
EMBED_API_BASE=<embeddings-endpoint-not-just-v1-base>
EMBED_API_KEY=<embedding-key>
```

For JiuwenMemory's default `APIEmbedding`, `EMBED_API_BASE` should be the embeddings endpoint itself, e.g. `http://127.0.0.1:18080/v1/embeddings` or `https://provider.example/v1/embeddings`.

## Minimal embedding probe

Before blaming Hermes, test the configured embedding endpoint directly without printing secrets:

```bash
python3 - <<'PY'
import json, urllib.request, urllib.error
from pathlib import Path
vals={}
for line in Path('~/.jiuwenmemory/.env').expanduser().read_text(errors='ignore').splitlines():
    s=line.strip()
    if not s or s.startswith('#') or '=' not in s:
        continue
    k,v=s.split('=',1)
    vals[k.strip()]=v.strip().strip('"').strip("'")
base=(vals.get('EMBED_API_BASE') or '').rstrip('/')
model=vals.get('EMBED_MODEL_NAME') or ''
key=vals.get('EMBED_API_KEY') or ''
req=urllib.request.Request(
    base,
    data=json.dumps({'model': model, 'input': 'ping'}).encode(),
    method='POST',
    headers={'Content-Type':'application/json', **({'Authorization':'Bearer '+key} if key else {})},
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        body=json.loads(r.read().decode())
    emb=(body.get('data') or [{}])[0].get('embedding') or body.get('embedding') or body.get('embeddings') or []
    print('embedding ok', 'dimension', len(emb) if hasattr(emb, '__len__') else 'n/a')
except urllib.error.HTTPError as e:
    print('embedding failed', e.code, e.read().decode(errors='ignore')[:500])
except Exception as e:
    print('embedding failed', type(e).__name__, str(e)[:500])
PY
```

If the provider's `/models` list contains no embedding-like models (`embedding`, `embed`, `bge`, `gte`, `e5`, `jina`), choosing `text-embedding-3-small` there will fail with `model_not_found`; use a different endpoint/key or add an embedding model to that gateway account group.

## Local BGE-M3 deployment path

For a no-external-key path, run a local OpenAI-compatible embeddings service and point `EMBED_API_BASE` to it. ModelScope has `BAAI/bge-m3`, and Huawei Modelers pages may mirror model metadata, but ModelScope is usually easier to automate from WSL.

A safe target shape:

```env
EMBED_MODEL_NAME=BAAI/bge-m3
EMBED_API_BASE=http://127.0.0.1:18080/v1/embeddings
EMBED_API_KEY=
```

Use an isolated venv under `~/.jiuwenmemory/embedding-server/`. Typical dependencies are `fastapi`, `uvicorn`, `modelscope`, and an embedding runtime such as `FlagEmbedding`/`torch`. Confirm disk and RAM first; BGE-M3 is much heavier than MiniLM-class embeddings.

## Hermes fallback vs native layered memory

A Hermes-side local fallback journal (for example `~/.hermes/jiuwenmemory_fallback.jsonl`) can prevent memory loss and provide lexical recall when the server embedding backend is broken. This is useful as a stopgap, but it is **not** JiuwenMemory's native L0-L3 layered memory, AutoDreaming, GraphMemory, or vector semantic recall.

Native layered memory requires the JiuwenMemory server's embedding call to succeed, followed by a server restart/reload if `~/.jiuwenmemory/.env` changed.

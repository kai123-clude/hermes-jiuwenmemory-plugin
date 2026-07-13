# JiuwenMemory AutoGenetic feature gaps: implementation and verification

Use this after the basic Hermes JiuwenMemory bridge and embedding backend are working (`jiuwenmemory_status` shows `memory_search: ok`) and the user asks whether article-level AutoGenetic Memory features are fully implemented.

## Current feature boundary to verify

A working bridge + BGE-M3 embeddings proves native vector search can run, but does **not** prove every article-level feature is enabled. Verify features separately:

- L0 raw message store: SQLite `user_message` rows with `message_id`, `user_id`, `scope_id`, `content`, `session_id`, `role`, `timestamp`.
- L1 summary: `get_user_mem_by_page(memory_type='summary')` and `/search_user_history_summary/` return records.
- L3 user profile: `get_user_mem_by_page(memory_type='user_profile')` and `/search_memory/` return records typed `user_profile`.
- L2 semantic/episodic: `semantic_memory` and `episodic_memory` must have records; do not infer from user_profile/summary.
- Auto Dreaming: the orchestrator must be running and sweeping; module existence is not enough.
- Graph Memory / Swarm / MemoryTurbo / benchmark metrics require separate implementation or measurement.

## Pitfall: preserve session_id

JiuwenMemory Dreaming groups records by `session_id` from the message store. If the Hermes provider discards `session_id`, or the HTTP server does not accept/pass it through, all messages collapse into `__default__` and Dreaming round filters/checkpoints become hard to reason about.

Implementation target:

1. Hermes provider `_JiuwenMemoryClient.add_messages(messages, session_id='')` includes `session_id` in the JSON payload when set.
2. `JiuwenMemoryProvider.sync_turn(..., session_id=...)` passes the session id instead of `del session_id`.
3. JiuwenMemory server `AddMessagesRequest` accepts `session_id` and passes it to `LongTermMemory.add_messages(...)` if the installed package supports that parameter. If not, inspect `MessageAddRequest`/`MessageManager` and add the field at the server/package layer.
4. Add tests proving payloads include `session_id` and that `sync_turn` forwards it.

## Enable Auto Dreaming

The installed JiuwenMemory package contains `DreamingConfig`, `DreamingOrchestrator`, `Sweeper`, `MessageStoreSessionSource`, and `MemoryUnitKnowledgeStore`, but the default `memory_server.py` startup path may not call `LongTermMemory.start_dreaming(...)` or expose HTTP controls.

Implementation target:

- Add env-driven startup flags to `memory_server.py`:
  - `DREAMING_ENABLED=true|false`
  - `DREAMING_SCOPE_ID=hermes`
  - `DREAMING_USER_ID=__default__` or the Hermes runtime user id if available
  - `DREAMING_INTERVAL_SECONDS=...`
  - `DREAMING_MIN_SESSION_ROUNDS=...`
  - `DREAMING_MAX_SESSIONS_PER_SWEEP=...`
  - `DREAMING_MAX_ITEMS_PER_SESSION=...`
- Add endpoints:
  - `POST /dreaming/start`
  - `POST /dreaming/stop`
  - `GET /dreaming/status`
- Status should expose `running`, `interval_seconds`, `scope_id`, `user_id`, and ideally checkpoint info.

Verification:

```bash
curl -sS http://127.0.0.1:8000/dreaming/status
journalctl --user -u jiuwen-memory-server.service -n 200 --no-pager | grep -i 'dreaming\|sweep\|promoted\|llm_call_end'
```

Pass criteria:

- `/dreaming/status` reports `running: true` and lists an orchestrator for the expected `scope_id`/`user_id`.
- Logs show `Dreaming started`, `llm_call_end` from the dreaming extraction prompt, and/or `dreaming: promoted N/M knowledge items`. Some package versions do not log literal `start sweep`/`sweep completed`, so do not require those exact strings if promotion and memory deltas are visible.
- `get_user_mem_by_page` counts increase or search results improve after one Dreaming interval.
- The checkpoint advances only after successful promotion when checkpoint access is available.

Pitfall: the `jiuwenmemory_store` Hermes tool can return fallback/timeout on long extraction even while the server and native search are healthy. For Phase A verification, use direct `/add_messages/`, `/search_memory/`, `/get_user_mem_by_page/`, `/dreaming/status`, and logs before concluding the embedding backend is broken.

## Verify L2 semantic and episodic memories

Preference tests usually become `user_profile` and `summary`; they are poor L2 tests. Use explicit facts with and without time anchors, and give the test a unique marker so results can be distinguished from old memories.

Semantic candidate:

```text
项目 Aurora 使用 FastAPI 作为后端框架，PostgreSQL 作为主数据库，Redis 用于缓存。
```

Episodic candidate:

```text
昨天我把 Aurora 项目的发布窗口从周三推迟到周五，因为支付网关回归测试失败。
```

Known-good write probe:

```bash
marker="phase-a-l2-verify-$(date +%Y%m%d)-aurora"
cat >/tmp/jiuwen_l2_payload.json <<JSON
{
  "scope_id": "hermes",
  "session_id": "$marker",
  "messages": [
    {
      "role": "user",
      "content": "项目 Aurora 使用 FastAPI 作为后端框架，PostgreSQL 作为主数据库，Redis 用于缓存。昨天我把 Aurora 项目的发布窗口从周三推迟到周五，因为 PaymentGateway 回归测试失败。验证标记 $marker。"
    },
    {
      "role": "assistant",
      "content": "已记录 Aurora 项目的技术栈、发布延期原因和验证标记。"
    }
  ],
  "enable_long_term_mem": true,
  "enable_user_profile": true,
  "enable_semantic_memory": true,
  "enable_episodic_memory": true,
  "enable_summary_memory": true
}
JSON
curl -fsS http://127.0.0.1:8000/add_messages/ \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/jiuwen_l2_payload.json
```

Verification endpoints:

```bash
curl -sS http://127.0.0.1:8000/get_user_mem_by_page/ \
  -H 'Content-Type: application/json' \
  -d '{"scope_id":"hermes","page_size":20,"page_idx":1,"memory_type":"semantic_memory"}'

curl -sS http://127.0.0.1:8000/get_user_mem_by_page/ \
  -H 'Content-Type: application/json' \
  -d '{"scope_id":"hermes","page_size":20,"page_idx":1,"memory_type":"episodic_memory"}'

curl -sS http://127.0.0.1:8000/search_memory/ \
  -H 'Content-Type: application/json' \
  -d '{"scope_id":"hermes","query":"Aurora 项目后端框架和延期原因是什么？","num":8,"threshold":0.0}'
```

Pass criteria:

- `semantic_memory total > 0` with stable project/technology facts.
- `episodic_memory total > 0` with dated/timeline event facts.
- `/search_memory/` can retrieve both with a natural-language query such as `Aurora 项目技术栈和延期原因是什么？`.
- If Dreaming is interval-based, wait one interval plus buffer (for example 70s when `DREAMING_INTERVAL_SECONDS=60`) and re-check; the initial synchronous write may produce some L2 facts before the Dreaming pass adds/refines more.

Observed Phase A pass shape from a working local BGE-M3 deployment:

```text
semantic_memory: Aurora uses FastAPI/PostgreSQL/Redis; PaymentGateway regression failed; marker captured.
episodic_memory: user postponed Aurora release because PaymentGateway regression failed; marker captured.
search_memory("Aurora 项目后端框架和延期原因是什么？") returned both semantic_memory and episodic_memory results.
```

## Graph Memory PoC before full integration

Do not claim Graph Memory is enabled just because graph modules exist. Prove entity/relation storage and query.

Minimal implementation target:

- Local SQLite graph tables are enough for a PoC: `entity`, `relation`, `episode`.
- Add endpoints: `POST /graph/extract`, `POST /graph/query`, `GET /graph/status`.
- Extract entities/relations with the configured LLM; store relation evidence and `session_id`.
- Later, add Hermes provider prefetch support for a `Relevant graph relations` block.

Verification scenario:

1. Write: `Aurora 项目依赖 PaymentGateway。PaymentGateway 回归测试失败导致 Aurora 发布延期。`
2. Query: `Aurora 依赖什么系统？为什么延期？`
3. Pass criteria: relation chain includes `Aurora -> depends_on -> PaymentGateway` and evidence/session id.

## MemoryTurbo implementation target

Treat MemoryTurbo as a performance/latency feature, not a correctness feature.

Implementation target:

- Add `/add_messages_async/`: write L0 raw messages and enqueue extraction, then return immediately.
- Use Dreaming or a queue worker to asynchronously promote structured memories.
- During the delay, retrieval should combine existing structured memories with recent raw/L0 cache so recall works before extraction finishes.

Verification:

- Compare p50/p95 latency for `/add_messages/` vs `/add_messages_async/`.
- Verify eventual consistency: immediate raw recall, later structured recall.
- Record LLM call count and token usage if the LLM client exposes usage; do not repeat article percentage claims without local benchmark data.

Observed PoC pass shape from the local server implementation:

- Endpoints: `POST /turbo/add_messages_async`, `GET /turbo/status`, `POST /turbo/process_once`.
- `/turbo/add_messages_async` should return quickly with `status: accepted`, `queued: true`, `job_id`, and `session_id`.
- `/turbo/status` should show the job progress through `queued`/`processing` to `completed` with `failed: 0` for the happy path.
- Search for the marker after completion should return native JiuwenMemory results, commonly `semantic_memory` plus `episodic_memory` for the test statement.
- `process_once` can correctly return `idle` if the background worker already claimed the job; verify final `/turbo/status`, not `process_once` alone.

## Swarm memory implementation target

Swarm requires multi-scope and access control. Start with a design, not direct global sharing.

Recommended scopes:

- `personal:{user_id}` for private user data.
- `team:{team_id}` for project/team facts.
- `org:{org_id}` for organization-wide reusable knowledge.

Implementation target:

- Promotion endpoint: `POST /swarm/promote` from source scope to target scope.
- ACL/sensitive-data filter before promotion.
- Hermes prefetch queries personal + team + org scopes and labels blocks separately.

Verification:

- Two users/agents: user B must not see user A personal memories.
- Both users can see team/org promoted memories.
- Sensitive facts are blocked or redacted before promotion.

Observed PoC verification pattern:

1. Promote a safe personal memory to `team:<id>` and a team memory to `org:<id>`.
2. Promote a note containing `password`, `secret`, `api key`, credit-card-like text, or 身份证-like text and verify it returns `skipped_sensitive` and never exposes `content` in public responses.
3. `/swarm/status` should show counts by `target_scope` and `status`, with recent promotion records omitting raw content.
4. `/swarm/search` with scopes `['team:<id>', 'org:<id>']` and shared query tokens should return promoted records grouped by scope.
5. `/swarm/search` with only `['personal:user-b']` should not return `personal:user-a` records.

Pitfall found in live verification: tests must search promoted SQLite records by query tokens using OR-style matching across `content`, `reason`, `mem_id`, and memory type. A too-strict AND token search can make `/swarm/status` show promoted counts while `/swarm/search` returns empty. Add a live-bug regression test with content like `Release checklist requires staged rollout. Swarm marker ...` and query `Release Swarm marker staged incident`.

## Benchmark/token claims

Article claims such as LoCoMo accuracy improvement or token reduction are not feature checks. They require a benchmark harness.

Minimum benchmark:

- Compare Hermes built-in memory, JiuwenMemory without Dreaming, and JiuwenMemory with Dreaming + local BGE-M3.
- Metrics: recall@k, MRR, answer accuracy/F1, prompt tokens, completion tokens, p50/p95 latency, write latency.
- Only report local measured deltas; do not reuse upstream percentage claims as if verified.

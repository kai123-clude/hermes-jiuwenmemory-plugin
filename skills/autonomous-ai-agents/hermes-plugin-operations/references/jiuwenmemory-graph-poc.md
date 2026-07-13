# JiuwenMemory Graph Memory PoC notes

Use this when continuing JiuwenMemory AutoGenetic/Graph Memory work for Hermes.

## Workflow preference

For Hermes plugin/JiuwenMemory coding work, the user prefers Hermes as orchestrator/planner/verifier and Codex as the code-writing agent. If the user says code should be handled by Codex, do not manually implement feature code in Hermes; start/monitor Codex, then independently verify tests and runtime behavior after Codex finishes.

## Phase B Graph Memory PoC shape

A minimal local Graph Memory PoC can live in the JiuwenMemory server layer when upstream graph modules are absent or not service-exposed.

Expected server behavior:

- SQLite DB under `~/.jiuwenmemory/graph_memory.sqlite3`.
- Endpoints:
  - `GET /graph/status`
  - `POST /graph/extract`
  - `POST /graph/query`
- Extract request supports:
  - `scope_id`, `user_id`, `session_id`, `text`
  - optional explicit `entities` and `relations`
- Persistence should deduplicate obvious duplicates:
  - entities: `name`, `type`, plus scope/user/session/evidence if implemented
  - relations: `source`, `target`, `relation_type`, `evidence`, `session_id`, `scope_id`, `user_id`
  - episodes: `session_id`, `content`, `scope_id`, `user_id`
- Query response should include matching/adjacent relation chains, evidence, and session IDs.

## Deterministic demo fixture

Use this graph fixture to verify relation-chain behavior:

```text
Aurora 项目依赖 PaymentGateway。PaymentGateway 负责人是 Alice。PaymentGateway 回归测试失败导致 Aurora 发布延期。
```

Expected query:

```text
Aurora 相关负责人是谁？为什么延期？
```

Expected relation evidence includes:

- `Aurora --depends_on--> PaymentGateway`
- `PaymentGateway --owner--> Alice`
- `PaymentGateway --caused_delay_of--> Aurora`
- chain path `Aurora -> PaymentGateway -> Alice`
- returned `session_id` from the extract call

## Verification commands

After Codex writes code, Hermes should verify, not assume:

```bash
python -m py_compile venv/lib/python3.11/site-packages/jiuwen_memory/server/memory_server.py
scripts/run_tests.sh tests/plugins/test_jiuwenmemory_plugin.py -q
```

If runtime verification requires restarting the systemd user service and approval blocks the command, stop and ask the user to approve or run manually. Do not retry the same restart via a different command.

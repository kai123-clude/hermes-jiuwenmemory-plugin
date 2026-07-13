# JiuwenMemory phased feature workflow notes

Use this when extending the local Hermes JiuwenMemory integration beyond basic provider enablement.

## User workflow preference

For Hermes/JiuwenMemory plugin or server coding tasks, the user prefers this split:

1. Hermes orchestrates: define the phase, scope, requirements, and verification criteria.
2. Codex writes/edits code. Do not keep hand-writing feature code in Hermes after the user says to let Codex handle coding.
3. Hermes independently verifies: inspect status, run targeted tests, restart services with user approval when required, and run end-to-end probes.
4. If a service restart is approval-gated, ask/obtain approval and do not retry the same restart command until approved.

Phrase waiting accurately: if Codex is still running, say it is running and that Hermes is polling/waiting. Do not say the work is stopped or paused unless the process was actually killed/stopped.

## Phase A: L2 + Dreaming verification shape

Prereqs: `jiuwenmemory_status` should report `memory_search: ok`, local BGE-M3 embedding server should be reachable, and JiuwenMemory server should be active.

Implementation targets already proven useful:

- Hermes provider forwards `session_id` in `add_messages` / `sync_turn`.
- JiuwenMemory server `AddMessagesRequest` accepts and forwards `session_id`.
- Server exposes `GET /dreaming/status`, `POST /dreaming/start`, `POST /dreaming/stop`.
- `DREAMING_*` env startup controls are loaded by the server.

Verification pass shape:

- Targeted tests: `scripts/run_tests.sh tests/plugins/test_jiuwenmemory_plugin.py -q`.
- Direct `/add_messages/` L2 probe with Aurora/FastAPI/PostgreSQL/Redis and PaymentGateway delay marker.
- Wait one Dreaming interval plus buffer when needed.
- Pass criteria: `semantic_memory` and `episodic_memory` totals increase and `/search_memory/` retrieves both semantic facts and episodic delay facts.

## Phase B: Graph Memory PoC shape

When upstream graph modules are absent or not service-wired, a minimal local PoC can be sufficient before claiming full Graph Memory:

- SQLite DB: `~/.jiuwenmemory/graph_memory.sqlite3`.
- Endpoints: `GET /graph/status`, `POST /graph/extract`, `POST /graph/query`.
- Persist entities, relations, and episodes with `scope_id`, `user_id`, `session_id`, and `evidence`.
- Deterministic extraction can cover demo/test entities such as Aurora, PaymentGateway, Alice, FastAPI, PostgreSQL, Redis.
- Query should return matching entities, adjacent relation chains, evidence, and session ids.

E2E verification scenario:

```text
Aurora 项目依赖 PaymentGateway。
PaymentGateway 负责人是 Alice。
PaymentGateway 回归测试失败导致 Aurora 发布延期。
Aurora 使用 FastAPI、PostgreSQL 和 Redis。
```

Pass criteria:

- `/graph/extract` returns `status: success`, `entities_written`, `relations_written`, and the provided `session_id`.
- `/graph/status` shows nonzero entities/relations/episodes.
- `/graph/query` for `Aurora 相关负责人是谁？为什么延期？` returns relations such as:
  - `Aurora --depends_on--> PaymentGateway`
  - `PaymentGateway --owner--> Alice`
  - `PaymentGateway --caused_delay_of--> Aurora`
  - `Aurora --uses--> FastAPI/PostgreSQL/Redis`
- Chains include `Aurora -> PaymentGateway -> Alice` and return evidence/session ids.

## Phase C1: MemoryTurbo PoC shape

Treat MemoryTurbo as a latency/queue PoC, not as proof of upstream article performance claims.

Minimal implementation target for Codex:

- SQLite queue/status DB, e.g. `~/.jiuwenmemory/memory_turbo.sqlite3`.
- `POST /turbo/add_messages_async`: accepts `/add_messages/` core payload plus `session_id`, persists raw messages immediately, returns quickly with `status: accepted`, `queued: true`, `job_id`, `session_id`.
- Worker/thread drains queued jobs in background; `POST /turbo/process_once` processes one pending job synchronously for deterministic tests/manual checks.
- `GET /turbo/status` returns queued/processing/completed/failed counts and recent jobs without secrets.
- Root endpoint lists turbo routes.

Verification pass shape:

- `python -m py_compile venv/lib/python3.11/site-packages/jiuwen_memory/server/memory_server.py`.
- `scripts/run_tests.sh tests/plugins/test_jiuwenmemory_plugin.py -q`.
- After approved service restart, E2E probe:
  1. `GET /turbo/status`.
  2. `POST /turbo/add_messages_async` with a unique marker/session id.
  3. Verify fast accepted/queued/job_id response.
  4. `POST /turbo/process_once` if the background worker has not completed it.
  5. Re-check `/turbo/status` for completed/failed counts.
  6. Verify JiuwenMemory health/search still reports `memory_search: ok`.

Do not repeat upstream claims like “80% latency reduction” or token reductions until a local benchmark measures them.

## Phase C2: Swarm Memory PoC shape

Swarm work should start as a scoped sharing/audit PoC, not direct unrestricted global memory sharing.

Minimal implementation target for Codex:

- SQLite promotion/audit DB, e.g. `~/.jiuwenmemory/swarm_memory.sqlite3`.
- `POST /swarm/promote`: promote a memory/content item from `source_scope` to `target_scope`; accept `content` when `mem_id` is not resolvable; include `memory_type`, `reason`, source/target user ids, and sensitivity.
- Reject or skip sensitive content using conservative heuristics for passwords, 身份证, credit-card-like strings, API keys, and `secret`-style tokens. Do not log secrets in responses.
- `GET /swarm/status`: return counts by target scope/status and recent records.
- `POST /swarm/search`: accept a list of scopes and query, then return scope-labeled promoted records; optionally combine native `/search_memory/`, but the PoC must work even if native search fails.
- Response shapes should document the convention: `personal:{user_id}`, `team:{team_id}`, `org:{org_id}`.
- Root endpoint lists swarm routes.

Verification pass shape:

- Targeted tests cover route presence, successful promotion, sensitive rejection, status counts, and multi-scope search behavior.
- E2E after approved service restart:
  1. Promote a team fact such as `Aurora 项目使用 FastAPI` from `personal:user-a` to `team:aurora`.
  2. Promote an org fact such as `BGE-M3 本地 embedding 服务监听 127.0.0.1:18080` to `org:hermes`.
  3. Attempt a sensitive personal promotion and verify it is rejected/redacted.
  4. Search with scopes `team:aurora, org:hermes` as another user and verify the team/org facts are visible.
  5. Search without `personal:user-a` and verify user A personal-only records are not returned.

Known-good live check shape from this session:

- Service prerequisites: `/health` returns healthy, `/swarm/status` returns available, and `jiuwen-memory-server.service` is active.
- Promote one record `personal:user-a -> team:alpha` with a unique team marker and one record `team:alpha -> org:acme` with a unique org marker.
- Attempt a sensitive promotion containing `password`, `secret`, and `API key`; the top-level response may be `status: "skipped"` while `record.status` is `"skipped_sensitive"`. Treat that as correct sensitive rejection rather than a failure.
- Search `scopes=['team:alpha','org:acme']` as `user-b`, then search `scopes=['personal:user-b']` as `user-b`.
- Pass criteria:
  - `team_count >= 1`
  - `org_count >= 1`
  - `personal_b_count == 0`
  - the sensitive marker is absent from the team/org search JSON
- Do not add an over-strict pass check that requires top-level sensitive status to equal `skipped_sensitive`; the durable contract observed here is top-level `skipped` plus `record.status: skipped_sensitive`.

Workflow pitfall: if a previous session recorded that a live verification script was approval-blocked, re-check current session state and user approval before treating the old block as a current limitation. Use session history to inherit context, but reconcile it with live service/status probes and current approvals before declaring work still blocked.

## Phase C3: benchmark/token/latency claims

Benchmark work should measure local deltas; never restate article percentages as verified facts.

Minimum benchmark harness:

- Compare synchronous `/add_messages/` vs Turbo `/turbo/add_messages_async` write latency p50/p95.
- Compare recall@k/MRR for built-in/fallback, JiuwenMemory native BGE-M3, and JiuwenMemory with Dreaming where possible.
- Track prompt/completion/total tokens only when logs or model responses expose real usage. If using Hermes' rough estimator (`agent.model_metadata.estimate_messages_tokens_rough`), label the numbers as rough preflight token estimates rather than provider billing tokens.
- Report exact dataset, run count, hardware/service mode, and confidence limits; label results as local measurements only.

Known-good first-pass token benchmark shape:

- Add an isolated operational script under the repo, e.g. `scripts/benchmark_jiuwenmemory_tokens.py`, rather than hand-running ad hoc snippets. The script should:
  - create a unique `scope_id` / marker / `session_id` per run so test facts do not collide with existing user memory;
  - synthesize a long conversation with a small number of explicit answerable facts plus verbose filler;
  - enqueue via `/turbo/add_messages_async`, then use `/turbo/process_once` and `/turbo/status` until the job reaches `completed` or times out;
  - query both `/search_memory/` and `/search_user_history_summary/`;
  - compare full raw-history prompt tokens with formatted recall-context tokens;
  - compute keyword hit rate, token reduction %, memory-search latency, and summary-search latency;
  - write a timestamped JSON result under `benchmark_results/`.
- A useful compact result line includes: `baseline_raw_history_tokens`, `avg_recall_context_tokens`, `avg_token_reduction_pct`, `avg_hit_rate`, `avg_search_memory_ms`, and `avg_search_summary_ms`.
- Example local first-pass result observed in this workflow: 64 synthetic messages, Turbo job completed in one attempt, rough raw-history tokens around 8k–30k depending on filler, recall context around 230–235 tokens, keyword hit rate 1.0, rough token reduction around 97–99%, memory search around 0.55–0.60s and summary search around 0.27s. Treat these as smoke evidence only; rerun on the current machine before quoting fresh numbers.

Verification discipline for benchmark-script edits:

- A benchmark script is code. After writing or changing it, do not stop at reporting an earlier live result; run fresh verification in the same turn:
  - `python -m py_compile scripts/benchmark_jiuwenmemory_tokens.py`
  - `python scripts/benchmark_jiuwenmemory_tokens.py --help`
  - `scripts/run_tests.sh tests/plugins/test_jiuwenmemory_plugin.py -q`
  - one small live run such as `python scripts/benchmark_jiuwenmemory_tokens.py --filler-repeat 2 --timeout 240`
- If the live run is blocked by service availability, report the concrete blocker and still include syntax/help + targeted test evidence.

### Real-session token benchmark shape

After a synthetic benchmark passes, verify token reduction against real Hermes history before claiming broader value:

- Read the canonical session store (`~/.hermes/state.db`) directly, selecting several sessions relevant to the memory domain by title/content keywords.
- Baseline = rough token estimate for the selected real user/assistant messages using `agent.model_metadata.estimate_messages_tokens_rough`.
- Recall path = live JiuwenMemory `/search_memory/` plus `/search_user_history_summary/` for a small set of domain queries.
- Compute and report: selected session count, selected message count, baseline real-history tokens, average recall-context tokens, token-reduction %, keyword hit rate, memory-search latency, summary-search latency, and the JSON result path.
- Do not print full raw session contents; keep sample recall context short and redact secret-like text.
- Treat Hermes rough estimates as preflight/context estimates, not provider billing tokens.

Known-good result shape from this workflow: 5 real JiuwenMemory-related sessions, 580 selected messages, baseline real-history tokens about 58.9k, average recall context about 708 tokens, token reduction about 98.8%, keyword hit rate 1.0, memory search about 0.62s, summary search about 0.30s. Rerun on the current machine before quoting fresh values.

## Productization: site-packages PoC persistence audit

When a JiuwenMemory server PoC is patched into the installed package under `venv/lib/python*/site-packages/jiuwen_memory/server/memory_server.py`, treat that as a high-risk persistence boundary: reinstalling/upgrading JiuwenMemory can erase Graph/Turbo/Swarm/Dreaming/session_id server changes.

Minimal productization step before moving on:

- Add or use a stdlib-only audit/export script such as `scripts/jiuwenmemory_server_audit.py`.
- The script should locate the installed `memory_server.py` without importing it, parse it with `ast`, and verify required PoC surface:
  - routes: `/turbo/add_messages_async`, `/turbo/status`, `/turbo/process_once`, `/swarm/promote`, `/swarm/status`, `/swarm/search`, `/graph/status`, `/graph/extract`, `/graph/query`, `/dreaming/status`, `/dreaming/start`, `/dreaming/stop`;
  - request models: Dreaming, Graph, and Swarm request classes;
  - `session_id` fields on `AddMessagesRequest` and `GraphExtractRequest`;
  - local persistence names such as `_GRAPH_DB_PATH`, `_TURBO_DB_PATH`, and `_SWARM_DB_PATH`.
- The export mode should write a timestamped direct backup, a full-file unified patch, and a manifest with source path, SHA-256, audit result, and artifact paths.
- Document the boundary in `plugins/memory/jiuwenmemory/SERVER_POC.md`: the plugin only calls the HTTP API; the server PoC lives in site-packages until upstreamed/forked.
- Verification pass shape:
  - `python -m py_compile scripts/jiuwenmemory_server_audit.py tests/scripts/test_jiuwenmemory_server_audit.py`
  - `python scripts/jiuwenmemory_server_audit.py verify --json` should report `ok: true`, `missing_count: 0`, and the live site-packages path.
  - `python scripts/jiuwenmemory_server_audit.py export --output-dir /tmp/... --timestamp ... --json` should create backup, patch, and manifest with matching SHA.
  - `scripts/run_tests.sh tests/scripts/test_jiuwenmemory_server_audit.py tests/plugins/test_jiuwenmemory_plugin.py -q` should pass.
  - Re-check `/health`, `/graph/status`, `/turbo/status`, `/swarm/status`, and the systemd service to confirm audit/export did not mutate runtime state.

This audit/export artifact is not the final upstream integration; it is a maintenance bridge. The next productization step is to migrate the server PoC into a durable fork/package or upstream patch.

## Repo hygiene and commit boundaries for JiuwenMemory productization

After PoC verification, sort the worktree so future reviews see source changes, not runtime debris:

- Keep these visible as source/commit candidates: `plugins/memory/jiuwenmemory/*`, `scripts/benchmark_jiuwenmemory_tokens.py`, `scripts/jiuwenmemory_server_audit.py`, `tests/plugins/test_jiuwenmemory_plugin.py`, and `tests/scripts/test_jiuwenmemory_server_audit.py`.
- Ignore generated/runtime state such as `.install_method` and root `benchmark_results/*.json`; do not delete the user's benchmark outputs just to clean `git status`.
- Add a README note that benchmark/audit scripts are source, while benchmark JSON reports are generated output.
- Before committing, run a secret-like string scan over candidate files. Treat variable names and test fake values as expected, but do not stage real credentials.
- Split commits by review boundary:
  1. Provider integration: `plugins/memory/jiuwenmemory/*` (except `SERVER_POC.md` if using a tooling commit), `hermes_cli/config.py`, env-registry tests, and provider/server tests.
  2. Audit/benchmark/hygiene: `.gitignore`, `SERVER_POC.md`, benchmark script, audit script, and audit tests.
- Exclude unrelated edits even if present in the worktree. Check `git diff --cached --name-only` before every commit and explicitly ensure unrelated files (for example `hermes_cli/setup.py` localization changes) are not staged.
- If git author identity is missing, set repo-local identity only (`git config user.name ...`, `git config user.email ...`), not global identity.
- Post-commit verification should include:
  - `scripts/run_tests.sh tests/plugins/test_jiuwenmemory_plugin.py tests/scripts/test_jiuwenmemory_server_audit.py tests/hermes_cli/test_config.py -q`
  - `python scripts/jiuwenmemory_server_audit.py verify --json`
  - `git show --pretty=format:'%h %s' --name-only <commit>` for each new commit, plus `git diff --name-only` to show intentionally remaining changes.

# Messaging query regression evidence — boilerplates#841

## Scope and reproducibility

Recorded 2026-11-07 UTC, macOS arm64 host, Python 3.14.7, Django 6.1.1,
PostgreSQL **17.11** in the isolated `django-837-pg` Docker container, 2 CPU /
512 MiB limit, tmpfs database, loopback-only randomly allocated port. Image:
`postgres:17-alpine`, local image ID
`sha256:9355df27b2506973cfc421408623435f15298511c2cdadc502b7aa580efe611f`.
No production data, persistent volumes, Redis or external delivery providers used.

Baseline application source: `3dbc55aa4a1bc58ebe47b3931dec2083a06e8987`.
The candidate adds regression tooling/bootstrap only: `messaging/views.py`,
serializers, models and migrations are **unchanged**. “Before/after” below means
baseline and final-tooling remeasurement of the same query implementation,
not a claimed optimization. No new index or query rewrite was justified.

Both performance runs used the same uninstrumented command (no coverage), Docker
instance, test fixtures, page size 20, warm-up request and five timed samples:

```bash
# Set isolated Docker DB variables as documented in README first.
uv run --locked pytest tests/test_messaging_queries.py tests/test_query_plans.py -q -s
```

pytest-django creates a separate test database and rolls datasets back. Three
synthetic users, two participants per conversation, alternating message senders;
all seeded conversations are visible to the measured user (broad-access case).
Bulk inserts are followed by ANALYZE. Each request is force-authenticated to
isolate application SQL; separate real-JWT tests assert the extra user lookup.
Median wall times include DRF serialization and local Docker transport, not only
SQL. EXPLAIN runs after sampling, with ANALYZE, BUFFERS and JSON output. Raw node
summaries include actual/estimated rows, loops, indexes, buffers and timing;
SQL/predicate identifiers and generated UUIDs are deliberately omitted.

## Measurements

| Dataset | Endpoint | SQL before → after | Median request ms before → after |
|---|---|---|---|
| 5 conversations / 50 messages | conversations | 4 → 4 | 4.440 → 6.122 |
| 5 conversations / 50 messages | messages | 2 → 2 | 2.304 → 4.031 |
| 1000 conversations / 20,000 messages | conversations | 4 → 4 | 8.122 → 9.415 |
| 1000 conversations / 20,000 messages | messages | 2 → 2 | 12.936 → 13.793 |

This is a local warm-cache observation, not a production latency SLO or a speedup
claim. Host scheduling/transport and dataset-dependent database work still affect
latency even though query count is constant. Timings are not CI pass thresholds.
A separate coverage-instrumented suite run is excluded from this comparison.

### Plan observations (same node structure before and after)

- Conversation SQL budget: COUNT, distinct paginated list, participant prefetch,
  latest-message prefetch = **4**. JWT adds one constant user SELECT = **5**.
- Message SQL budget: COUNT, page joined to sender/conversation = **2**. JWT = **3**.
- Small dataset: sequential scans/hash joins are appropriate for tiny relations;
  WindowAgg reduces 50 messages to 5 latest-message rows.
- Large conversation list: COUNT/list visit 1000 visible conversations. The
  participant prefetch uses `conversations_participants_conversation_id_988acf55`
  and returns 40 rows. Latest-message prefetch uses bitmap access via
  `messages_conversation_id_5ef638db`, processes **400** messages (20 page rooms ×
  20 messages), then WindowAgg returns **20** rows. It does not load all 20,000
  messages into Python. Existing composite `(conversation, created_at)` index
  remains available; PostgreSQL chose the existing FK index for this workload.
- Large message list: joins/COUNT scan **20,000** visible messages; a top-N sort
  supplies 20 page rows. After-run SQL EXPLAIN execution times were **4.474 ms**
  for COUNT and **11.491 ms** for the page (before: 4.205 / 11.601 ms).
  Constant SQL count does **not** mean constant database work. Conversation-scoped
  filtering/cursor pagination/global ordering indexes would need a separate
  workload-driven decision; no speculative API/index change here.
- Large conversation after-run EXPLAIN execution times in budget order:
  **0.622 / 0.426 / 0.057 / 0.354 ms** (before: 0.571 / 0.441 / 0.045 / 0.325).

## Retained evidence and regression boundaries

- [Before, small](query-plans/before-small.json)
- [Before, large](query-plans/before-large.json)
- [After, small](query-plans/after-small.json)
- [After, large](query-plans/after-large.json)

`tests/test_messaging_queries.py` asserts exact budgets at 1/20/45 conversations,
including second pages and pagination COUNT, empty-room last_message, latest
message IDs/sender phone, membership and outsider exclusion. Real-JWT cases
protect the authentication-inclusive budgets. `tests/test_business.py` covers
owner/sender mutation and cross-user access independently. Plan tests also assert
counts, page sizes and budgets at both dataset sizes; they intentionally do not
assert PostgreSQL's exact plan choice across versions or hardware.

# Data Collection Implementation Plan — v1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可独立运行、可测试、可替换 Data Source Adapter 的 Data Collection 模块，并在不登录金融账户、不自动交易的前提下，为当前 9 个基金、版本化定投、月度账户确认、质量/新鲜度/对账 Gate、Raw Evidence、Canonical Snapshot、版本化 contract 与农业银行债券公开报价池提供可靠基础。

**Architecture:** 采用模块化单体 + 独立 Worker + PostgreSQL 分 Schema + Port / Adapter + Transactional Outbox。Data Collection 内部按 `domain → application → ports → adapters` 分层，外部数据只能通过 Adapter 进入；Portfolio Ledger、Valuation、Risk、Bond、Rebalance 不得读取 Data Collection 内部表。

**Tech Stack:** Python 3.12+、FastAPI、Pydantic 2、SQLAlchemy 2、Alembic、PostgreSQL 16+、psycopg 3、Jinja2、HTMX、pytest、PostgreSQL integration test fixture、Ruff、mypy。

**Spec:** `docs/superpowers/specs/2026-09-12-data-collection-design.md`

**Status:** `DATA_COLLECTION_IMPLEMENTATION_PLAN_APPROVED`

**PROJECT_ID:** `PRJ-ASSET-MGMT-20260912-001`

**PROJECT_CONTEXT_ID:** `43e85b1a-131b-4897-aa89-9b250d59fde0`

## Global Constraints

- 金额、价格、份额使用 Python `Decimal` 与 PostgreSQL `NUMERIC`；禁止使用 binary float 保存金融值。
- 所有金融金额和份额计划使用 `NUMERIC(28, 10)`；业务日期使用 `DATE`；精确时间使用 `TIMESTAMPTZ`。
- 第一版不建设独立 React SPA；内部 UI 使用 Jinja2 + HTMX。
- Data Collection 只写自己的 `data_collection` schema；下游只能通过 versioned contracts、events 或 public projections 访问。
- 不登录任何银行、券商或其他金融账户；不存储凭据、密码、OTP、Cookie 或金融账户 token。
- 不实现自动交易，不提供 `place_order`、`buy`、`sell`、`redeem`、`subscribe_fund` 等交易执行能力。
- TDD mandatory：每个实现任务按 failing test → 验证失败 → 最小实现 → 验证通过 → focused commit 执行。
- 计划中的依赖只是获批的 implementation plan 内容；本计划发布 Work Unit 禁止安装依赖。
- Source Permission Audit 之前，不得将 public source 改为 `AUTO_ALLOWED`；先 manual parser，再 contract tests，再单独批准自动采集。
- `DAILY != TRADING_DAY`；计划估算不得自动升级为 Account Fact；月度确认 `confirmed_units` 必填。
- Quality、Freshness、Reconciliation 是三个独立 Gate；数据不足语义为 `NOT_EVALUATED`，不是 `NOT_RECOMMENDED`。
- 所有正式计算未来必须绑定 Snapshot；Adapter 可替换且不得污染 Domain/Core。

## Planned Repository Structure

后续实现预计创建以下文件与目录；本计划发布 Work Unit 不创建它们：

```text
pyproject.toml
src/asset_management/
  config.py
  app.py
  data_collection/
    domain/
    contracts/v1/
    ports/
    application/
    adapters/
  web/routes/
  web/templates/data_collection/
alembic/
  env.py
  versions/
tests/
  unit/data_collection/
  contract/data_collection/
  integration/data_collection/
  web/
```

## Planned Data Collection Schema

后续只创建 PostgreSQL `data_collection` schema，内部表为：

`data_source`、`tracked_instrument`、`market_calendar_day`、`investment_plan_version`、`planned_contribution`、`raw_evidence`、`market_observation`、`monthly_reconciliation_cycle`、`monthly_account_anchor`、`reconciliation_adjustment`、`canonical_snapshot`、`data_quality_alert`、`collection_run`、`outbox_event`、`abc_quote_snapshot`、`abc_quote_entry`。

本计划发布 Work Unit 不执行 migration。

## Implementation Tasks

### Task 1 — Application Scaffold

**Files:**

- Create later: `pyproject.toml`, `src/asset_management/config.py`, `src/asset_management/app.py`, `tests/conftest.py`, `tests/test_app_boot.py`

**Interface and acceptance:** 建立最小 FastAPI 应用、配置入口、测试 fixture 与 boot test；不引入金融业务逻辑。测试先验证应用 import/boot 失败，再以最小实现通过。

- [ ] Write `tests/test_app_boot.py` failing test for app import and health/boot behavior.
- [ ] Run `pytest tests/test_app_boot.py -v`; expected result is a focused failure before implementation.
- [ ] Add the minimal scaffold and configuration boundary.
- [ ] Run the focused test and then the complete scaffold test set; expected result is PASS.
- [ ] Commit `feat: bootstrap modular asset management application`.

### Task 2 — Domain Enums and Versioned Contracts

**Files:**

- Create later: `src/asset_management/data_collection/domain/`, `src/asset_management/data_collection/contracts/v1/`
- Tests later: `tests/unit/data_collection/`, `tests/contract/data_collection/`

**Interfaces:** 定义 `SourcePolicy`、`ScheduleType`、`PlanStatus`、`ContributionStatus`、`QualityStatus`、`FreshnessStatus`、`ReconciliationStatus`、`PortfolioConfidence`、`CalendarAlignmentStatus`、`QuoteAvailabilityStatus`、`ConfirmationLevel`；创建 `ValidatedMarketObservation.v1`、`AccountImportEnvelope.v1`、`InvestmentPlanSnapshot.v1`、`MonthlyAccountAnchor.v1`、`ABCDailyTradableUniverseSnapshot.v1`、`CollectionRunStatus.v1`、`DataQualityAlert.v1`。

**Invariants:** `estimated_units != confirmed_units`；不得以缺少确认等级的单一 `units` 字段替代二者。

- [ ] Write contract tests for schema, required fields, Decimal values, enum values, fixed v1 version, and the estimated/confirmed units separation.
- [ ] Run the contract tests and verify the intended failures.
- [ ] Add the smallest domain enums and Pydantic v1 contracts.
- [ ] Run unit and contract tests; expected result is PASS.
- [ ] Commit `feat: define data collection v1 contracts`.

### Task 3 — PostgreSQL Data Collection Schema

**Files:**

- Create later: `alembic/env.py`, `alembic/versions/<data_collection_revision>.py`
- Tests later: `tests/integration/data_collection/`

**Interfaces and database rules:** 只创建 `data_collection` schema 与计划表；所有金融金额和份额为 `NUMERIC(28, 10)`。Migration 必须约束 `confirmed_units >= 0`、`account_value >= 0`、`pending_amount >= 0`、`pending_units >= 0`、`investment amount >= 0`，并支持真实 PostgreSQL integration fixture。

- [ ] Write integration tests against real PostgreSQL for schema ownership, numeric precision, non-negative constraints, and absence of unrelated business schemas.
- [ ] Run the integration tests and verify failure before migration.
- [ ] Add the minimal schema migration.
- [ ] Run integration tests and `alembic upgrade head`, `alembic downgrade base`, `alembic upgrade head`; expected result is PASS.
- [ ] Commit `feat: add data collection persistence schema`.

### Task 4 — Source Registry and Tracked Instruments

**Files:**

- Create later: registry models, seed module, and related migration/data fixture under `src/asset_management/data_collection/` and `alembic/versions/`
- Tests later: source and instrument registry unit/integration tests

**Seed contract:** 注册 `CN_TRADING_CALENDAR`，`policy = MANUAL_DOWNLOAD`；不得自动联网获得日历。当前 9 个 Tracked Instruments 为 `019172`、`017641`、`016452`、`021707`、`000307`、`020602`、`161130`、`161125`、`002963`，初始 `verification_status = UNVERIFIED`。

**Identity rule:** 不根据代码猜基金名称、类别或跟踪指数；未经证据验证的身份保持未验证。

- [ ] Write tests for exact nine-code seed, manual calendar policy, and unverified identity status.
- [ ] Run them and verify the expected failing seed behavior.
- [ ] Add the minimum registry and seed implementation.
- [ ] Run focused tests and database checks; expected result is PASS.
- [ ] Commit `feat: add source and tracked instrument registries`.

### Task 5 — Raw Evidence Store

**Files:**

- Create later: `src/asset_management/data_collection/ports/raw_evidence_store.py`, `src/asset_management/data_collection/adapters/filesystem_raw_evidence_store.py`
- Tests later: `tests/unit/data_collection/test_raw_evidence_store.py`

**Interface:** `RawEvidenceStore.put(...)` and `RawEvidenceStore.get(...)`；首个 Adapter 为 `FilesystemRawEvidenceStore`。内容使用 SHA-256 标识，存储必须 immutable、可重读、可校验、不静默覆盖，metadata 必须与文件一致。

- [ ] Write tests for put/get round-trip, SHA-256 identity, metadata consistency, immutable duplicate write rejection, and corruption detection.
- [ ] Run the focused tests and verify failure before implementation.
- [ ] Add the port and filesystem adapter with deterministic content addressing.
- [ ] Run the focused tests; expected result is PASS.
- [ ] Commit `feat: add immutable raw evidence storage`.

### Task 6 — Investment Plan Versioning

**Files:**

- Create later: investment plan domain/application/persistence components and migration
- Tests later: `tests/unit/data_collection/test_investment_plan_versioning.py`, contract/integration coverage

**Approved initial plans:**

```text
019172 = TRADING_DAY 10 RMB ENABLED
017641 = TRADING_DAY 10 RMB ENABLED
016452 = DAILY 40 RMB ENABLED
021707 = DAILY 10 RMB ENABLED
000307 = DAILY 10 RMB ENABLED
020602 = TRADING_DAY 10 RMB ENABLED
161130 = NONE 0 RMB HELD_ONLY
161125 = NONE 0 RMB HELD_ONLY
002963 = NONE 0 RMB HELD_ONLY
```

**Operation:** `change_plan(instrument_code, schedule_type, amount, effective_from)`；必须 close previous `effective_to`、create new version、保留历史版本、拒绝重叠日期范围；暂停同样创建新版本。`DAILY` 与 `TRADING_DAY` 永久独立。

- [ ] Write failing tests for initial nine-plan baseline, effective boundaries, historical preservation, overlap rejection, and pause-as-new-version.
- [ ] Run focused tests and verify failure.
- [ ] Implement the minimum versioned domain operation and persistence.
- [ ] Run focused unit/contract/integration tests; expected result is PASS.
- [ ] Commit `feat: implement versioned investment plans`.

### Task 7 — Planned Contribution Generation

**Files:**

- Create later: contribution generation application service and repository components
- Tests later: `tests/unit/data_collection/test_planned_contributions.py`, integration coverage

**Interface:** `generate_planned_contributions(target_date)`。

**Rules:** `DAILY` 按 calendar date 生成；`TRADING_DAY` 仅在 `market_calendar_day.is_trading_day == true` 时生成。事件支持 `PLANNED`、`EXPECTED`、`PENDING_CONFIRMATION`、`PROVISIONAL`，不得由计划生成 `CONFIRMED units`，并且必须幂等。

- [ ] Write tests for working day, weekend, holiday, rerun, paused plan, and effective-date boundary.
- [ ] Run focused tests and verify failure.
- [ ] Add deterministic, idempotent generation.
- [ ] Run focused and integration tests; expected result is PASS.
- [ ] Commit `feat: generate deterministic planned contributions`.

### Task 8 — Data Quality Gate

**Files:**

- Create later: quality domain service and alert persistence components
- Tests later: `tests/unit/data_collection/test_quality_gate.py`

**Interface:** `evaluate_quality(observation)`；状态为 `VERIFIED`、`VALID`、`SUSPECT`、`CONFLICT`、`INVALID`、`QUARANTINED`。

**Checks:** format、dates、numeric range、instrument identity、duplicate、semantic consistency、temporal discontinuity、same-semantic-source conflict。ABC customer quote 与 ChinaBond market valuation 数值不同不得直接判为 `CONFLICT`；明显数量级跳变可判 `SUSPECT`；不得自动修改数据。

- [ ] Write tests for every listed check, including the ABC/ChinaBond semantic distinction and no-mutation behavior.
- [ ] Run them and verify failure.
- [ ] Implement the independent quality service.
- [ ] Run focused tests; expected result is PASS.
- [ ] Commit `feat: implement data quality gate`.

### Task 9 — Freshness Gate

**Files:**

- Create later: calendar-aware freshness service
- Tests later: `tests/unit/data_collection/test_freshness_gate.py`

**Interface:** `evaluate_freshness(observation, evaluation_time, market_calendar)`；状态为 `FRESH`、`STALE`、`EXPIRED`、`UNKNOWN`、`MISSING`。

**Rules:** 禁止只用 `now - collected_at`；ETF 周六的最新周五收盘价可为 `FRESH`；ABC quote 在非当前有效交易日不得冒充当前报价；只有日期没有 quote time 不得宣称 `REALTIME`；QDII 支持 `ALIGNED`、`PARTIALLY_ALIGNED`、`MISALIGNED`、`UNKNOWN`。

- [ ] Write tests for weekends, holidays, quote time absence, ABC current-day restriction, ETF close handling, and QDII alignment.
- [ ] Run focused tests and verify failure.
- [ ] Implement the calendar-aware freshness service.
- [ ] Run focused tests; expected result is PASS.
- [ ] Commit `feat: implement calendar-aware freshness gate`.

### Task 10 — Monthly Reconciliation Cycle

**Files:**

- Create later: monthly cycle domain/application components and migration
- Tests later: `tests/unit/data_collection/test_monthly_reconciliation_cycle.py`

**Rule:** 默认 `FIRST_CN_NON_TRADING_DAY_AFTER_MONTH_END`；系统只计算建议确认窗口。`confirmed_at` 不等于 `snapshot_as_of_date`。month end Friday → Saturday preferred confirmation day；month end Sunday → Sunday itself may be confirmation day。

- [ ] Write failing tests for month-end Friday, month-end Sunday, dates crossing month/year, and timestamp/date separation.
- [ ] Run focused tests and verify failure.
- [ ] Implement cycle calculation and preferred-window output.
- [ ] Run focused tests; expected result is PASS.
- [ ] Commit `feat: add monthly reconciliation cycles`.

### Task 11 — Monthly Account Anchor

**Files:**

- Create later: monthly anchor domain/contract/application components
- Tests later: `tests/contract/data_collection/test_monthly_account_anchor.py`, unit/integration coverage

**Required fields:** `instrument_code`、`account_value`、`confirmed_units`、`snapshot_as_of_date`。

**Optional fields:** `pending_amount / pending_units`（二者可分别已知或未知）。

**Authority rules:** 生成 `MonthlyAccountAnchor.v1`；用户月度事实 Authority 高于系统估算；禁止 `estimated_units` 自动成为 `confirmed_units`；必须支持 `pending_amount known` 且 `pending_units unknown`。

- [ ] Write contract tests for required/optional fields, Decimal values, pending asymmetry, and rejection of estimated-to-confirmed promotion.
- [ ] Run focused tests and verify failure.
- [ ] Implement anchor creation and v1 serialization.
- [ ] Run unit/contract tests; expected result is PASS.
- [ ] Commit `feat: add monthly account anchors`.

### Task 12 — Reconciliation Gate

**Files:**

- Create later: reconciliation service, configurable thresholds, adjustment persistence
- Tests later: `tests/unit/data_collection/test_reconciliation.py`, integration coverage

**Operation:** 比较 `system estimated position` 与 `MonthlyAccountAnchor`；状态为 `RECONCILED`、`MINOR_DIFFERENCE`、`MATERIAL_DIFFERENCE`、`UNRESOLVED`。threshold 必须配置化，差异产生 `reconciliation_adjustment`。

**Immutability:** 禁止修改 historical plan version、historical planned contribution、historical anchor；新的 Anchor 成为下一周期估算起点。

- [ ] Write tests for all statuses, configurable thresholds, adjustment creation, and historical immutability.
- [ ] Run focused tests and verify failure.
- [ ] Implement the independent reconciliation gate.
- [ ] Run focused/integration tests; expected result is PASS.
- [ ] Commit `feat: implement monthly reconciliation`.

### Task 13 — Market Observation and Canonical Snapshot

**Files:**

- Create later: observation normalization, snapshot builder, provenance models and persistence
- Tests later: quality/freshness/snapshot contract and integration tests

**Pipeline:** `Raw Evidence → Normalized Observation → Quality Gate → Freshness Gate → Canonical Snapshot`。

`SUSPECT`、`CONFLICT`、`INVALID`、`QUARANTINED` 不得进入正式 canonical usable data；`STALE` 可保存但必须继续标记 `STALE`。Snapshot 必须追踪 source provenance、raw evidence、parser version、quality、freshness、reconciliation。

- [ ] Write failing tests for the pipeline, rejected statuses, retained stale marking, and complete provenance.
- [ ] Run focused tests and verify failure.
- [ ] Implement the minimum normalized observation and snapshot builder.
- [ ] Run focused/contract/integration tests; expected result is PASS.
- [ ] Commit `feat: build canonical data snapshots`.

### Task 14 — Transactional Outbox

**Files:**

- Create later: outbox port/application/persistence components and transaction integration
- Tests later: `tests/integration/data_collection/test_transactional_outbox.py`

**Transaction contract:** 同一个 PostgreSQL transaction 内保存 `canonical data + outbox_event`；禁止调用未来 Portfolio Ledger 内部函数。Outbox fields 为 `event_id`、`contract_name`、`contract_version`、`aggregate_id`、`occurred_at`、`payload`。

Rollback 时两者必须一起 rollback。

- [ ] Write integration tests for atomic commit, rollback of both records, exact outbox fields, v1 contract payload, and absence of downstream internal calls.
- [ ] Run them and verify failure.
- [ ] Implement the transactional outbox boundary.
- [ ] Run integration tests; expected result is PASS.
- [ ] Commit `feat: publish data collection contracts through outbox`.

### Task 15 — ABC Daily Quote Universe Core

**Files:**

- Create later: ABC quote core models, contracts, repository and migration
- Tests later: ABC quote unit/contract/integration coverage

**Scope:** 此任务只建设 Core model；禁止实现 ABC 自动网页登录或账户登录。支持 `ABCDailyTradableUniverseSnapshot.v1`，内部表为 `abc_quote_snapshot`、`abc_quote_entry`。

**Statuses:** `BUY_QUOTED`、`SELL_QUOTED`、`TWO_WAY_QUOTED`、`NO_CURRENT_QUOTE`。

理论 Strategy Universe 与 ABC execution candidate universe 必须独立；不得使用 `GUARANTEED_TRADABLE`。ChinaBond、ChinaMoney、ABC source parser 放入独立 Source Adapter Plan。

- [ ] Write tests for the v1 snapshot, quote availability statuses, independent universes, and forbidden guaranteed-tradable semantics.
- [ ] Run focused tests and verify failure.
- [ ] Implement only the core models and contracts.
- [ ] Run focused/contract/integration tests; expected result is PASS.
- [ ] Commit `feat: model ABC daily quoted bond universe`.

### Task 16 — Investment Plan UI

**Files:**

- Create later: `src/asset_management/web/routes/` investment-plan routes and `src/asset_management/web/templates/data_collection/` templates
- Tests later: `tests/web/`

**Routes:** `GET /data-collection/investment-plans`、`POST /data-collection/investment-plans/{instrument_code}`、`GET /data-collection/investment-plans/{instrument_code}/history`。

页面支持当前 9 个基金、enable/pause、schedule、amount、effective date、history、estimated monthly contribution；禁止提供覆盖历史功能。这是系统内部 UI route，不是第三方金融 API。

- [ ] Write failing web tests for listing, versioned update, pause, history, and no-history-overwrite behavior.
- [ ] Run focused web tests and verify failure.
- [ ] Implement the minimum Jinja2 + HTMX routes and templates.
- [ ] Run web tests; expected result is PASS.
- [ ] Commit `feat: add investment plan management page`.

### Task 17 — Monthly Confirmation UI

**Files:**

- Create later: monthly-confirmation route and template
- Tests later: `tests/web/test_monthly_confirmation.py`

**Routes:** `GET /data-collection/monthly-confirmation`、`POST /data-collection/monthly-confirmation`。

自动列出 held funds。输入 `account_value REQUIRED`、`confirmed_units REQUIRED`、`pending_amount OPTIONAL`、`pending_units OPTIONAL`、`snapshot_as_of_date REQUIRED`。显示 previous Anchor、expected contribution、pending estimate、preferred non-trading-day window。提交结果显示 reconciliation status、unit difference、account-value difference、pending difference、new Anchor ID。

- [ ] Write failing web tests for required confirmation fields, held-fund listing, pending asymmetry, and result display.
- [ ] Run focused web tests and verify failure.
- [ ] Implement the minimum confirmation UI over the anchor/reconciliation application interfaces.
- [ ] Run web tests; expected result is PASS.
- [ ] Commit `feat: add monthly account confirmation page`.

### Task 18 — Idempotent Worker Commands

**Files:**

- Create later: callable job modules under `src/asset_management/data_collection/application/`
- Tests later: `tests/unit/data_collection/test_jobs.py`, integration retry tests

Data Collection 不承担永久 schedule orchestration，只提供 callable jobs：`generate_planned_contributions`、`evaluate_market_observations`、`build_market_snapshot`、`open_monthly_reconciliation_cycle`。

每个 job 必须 deterministic、idempotent、retry-safe。

- [ ] Write failing tests for deterministic output, rerun idempotency, and safe retry after partial failure.
- [ ] Run focused tests and verify failure.
- [ ] Expose the four callable jobs using existing application ports.
- [ ] Run unit/integration job tests; expected result is PASS.
- [ ] Commit `feat: expose idempotent data collection jobs`.

### Task 19 — Security Boundary Tests

**Files:**

- Create later: `tests/unit/data_collection/test_security_boundaries.py`, repository-wide security checks

测试必须自动禁止 bank login、broker login、credential table、password model、OTP model、Cookie model、financial-account token storage、trade execution adapter，以及 `place_order`、`buy`、`sell`、`redeem`、`subscribe_fund`。

- [ ] Write repository and API-surface tests for each forbidden capability and storage shape.
- [ ] Run them and verify failure against any accidental boundary violation.
- [ ] Add only the minimum guard tests or deny-list validation required by the project.
- [ ] Run security boundary tests and full regression tests; expected result is PASS.
- [ ] Commit `test: enforce financial account safety boundaries`.

### Task 20 — End-to-End Acceptance

**Files:**

- Create later: `tests/integration/data_collection/test_acceptance.py`
- Verify later: application, migration, schema, worker, UI and contract paths created by Tasks 1–19

**Scenario:**

1. Seed 9 funds。
2. Load CN trading calendar fixture。
3. Generate planned contributions。
4. Save market observation。
5. Quality PASS。
6. Freshness PASS。
7. Build market snapshot。
8. Enter monthly account confirmation。
9. `confirmed_units` required。
10. Preserve pending QDII contribution。
11. Reconcile。
12. Build `MonthlyAccountAnchor`。
13. Publish outbox contract。

同时验证 `SUSPECT` data 不进入正式 snapshot；`STALE` / insufficient data 保留未来 `NOT_EVALUATED`，不得变成 `NOT_RECOMMENDED`。

- [ ] Write the complete acceptance test and verify the initial failure.
- [ ] Run the acceptance test against real PostgreSQL and verify failure before missing implementation is added.
- [ ] Complete only the minimal missing integration wiring.
- [ ] Run the full verification set: `pytest -v`; `ruff check .`; `mypy src`; `alembic upgrade head`; `alembic downgrade base`; `alembic upgrade head`; `git diff --check`; `validate_project.py`.
- [ ] Commit `test: complete data collection acceptance coverage`.

## Source Adapter Plans

Data Collection Core 完成后，采集器必须单独规划。

### Plan B — Fund / Gold Source Adapters

范围：fund NAV、ETF close、gold ETF reference、SGE reference、instrument identity verification。

每个 source 按 `Source Permission Audit → manual parser → contract tests → separately approve AUTO_ALLOWED` 执行。

### Plan C — Bond Source Adapters

范围：ChinaBond valuation、ChinaBond yield curve、ChinaMoney bond master、ABC product universe、ABC daily quotes。

同样按 `Source Permission Audit → manual parser first → tests → separately decide AUTO_ALLOWED` 执行。

单一 Adapter 失败不得要求 Core 修改。

## Implementation Work Units

批准后的开发拆为：

| Work Unit | Tasks | Scope |
|---|---:|---|
| `WU-DC-CORE-01` | 1–5 | Application scaffold、contracts、database schema、registries、Raw Evidence |
| `WU-DC-CORE-02` | 6–12 | Investment plans、contribution generation、Quality Gate、Freshness Gate、monthly cycles、anchors、reconciliation |
| `WU-DC-CORE-03` | 13–18 | Canonical Snapshot、Outbox、ABC Quote Universe Core、Investment Plan UI、Monthly Confirmation UI、Worker jobs |
| `WU-DC-CORE-04` | 19–20 | Security boundary、full integration、acceptance、production readiness |

每个 WU 都必须经过 `TDD → focused commits → unit tests → contract tests → integration tests → publication → GPT independent verification → next WU`，不得跳过 Work Unit Gate。

## Global Implementation Rules

1. TDD mandatory。
2. 每个实现任务：failing test → verify failure → minimal implementation → verify pass → focused commit。
3. 金融金额禁止 binary float。
4. Data Collection 只写自己的 schema。
5. 下游禁止读取 Data Collection internal tables。
6. 不允许金融账户登录。
7. 不允许自动交易。
8. 不允许计划估算自动升级 Account Fact。
9. `confirmed_units` 月度必填。
10. `DAILY` 与 `TRADING_DAY` 永久独立。
11. Quality / Freshness / Reconciliation 是独立 Gate。
12. 数据不足为 `NOT_EVALUATED`，不是 `NOT_RECOMMENDED`。
13. 所有正式计算未来必须绑定 Snapshot。
14. Source Permission Audit 之前不得擅自把 public source 改为 `AUTO_ALLOWED`。
15. Adapter 可替换，不允许污染 Domain/Core。

## Implementation Plan Approval Gate

本计划已经获得用户批准，但本 Work Unit 只允许发布实施计划文档。计划 publication 完成并由 GPT 独立核验之前，禁止启动 `WU-DC-CORE-01`。

## Plan Self-Review

发布前必须逐项确认：

1. Spec path 为 `docs/superpowers/specs/2026-09-12-data-collection-design.md`。
2. `PROJECT_CONTEXT_ID` 为 `43e85b1a-131b-4897-aa89-9b250d59fde0`。
3. 当前 9 个基金规则准确。
4. `DAILY != TRADING_DAY`。
5. `confirmed_units` 月度必填。
6. QDII pending amount / pending units 支持。
7. Quality/Freshness/Reconciliation 三个 Gate 独立。
8. Raw Evidence 存在。
9. Canonical Snapshot 存在。
10. ABC quote universe 不声称 guaranteed tradable。
11. Source Permission Audit 在自动采集之前。
12. 金融账户登录被禁止。
13. 自动交易被禁止。
14. 数据不足 = `NOT_EVALUATED`。
15. Source Adapter 分 Plan B / Plan C。
16. `WU-DC-CORE-01..04` 清晰拆分。
17. 没有业务代码被创建。

占位符扫描必须为 0 matches；本计划已避免使用任何占位符标记。

## Verification and Publication

### Verification

执行 `git diff --check`，再执行：

```text
python D:\资产管理\_gpt-codex-framework-readonly\.gpt-codex\scripts\validate_project.py .
```

必须返回 `RESULT: PASS`。changed files 只允许实施计划文档与本 Work Unit 所需治理文件；不得出现 `src/`、`tests/`、`alembic/`、`pyproject.toml`、业务代码、数据库 migration、UI 或业务 dependency。

### Publication Sequence

按 Framework continuity contract 执行 bounded `W → P → live observation`：

1. 创建 Work Commit W，建议 message：`docs: add approved data collection implementation plan`。
2. W 只包含 `docs/superpowers/plans/2026-09-12-data-collection-implementation.md` 与该 Work Unit 所需 work/evidence 文件。
3. 完成 live remote verification。
4. 创建 management-only Publication Commit P，建议 message：`chore: publish data collection implementation plan`。
5. P 仅包含 `STATE`、Result Envelope、Evidence publication bookkeeping 以及 Framework 要求的 management-only 内容。
6. 禁止 force push、history rewrite、amend published history、rebase published history、其他 branch 修改。
7. 最后 live observe `origin/main`，确认远端 ref head 等于 P，且 W/P 可达、结果文件存在；P 不写入自己的 SHA。

### Final State

完成后保持：

```text
state = AUTHORIZED
active_work_unit = null
blockers = []
continuity.sync_status = SYNCED
```

STATE revision 合法递增；`next_action` 必须为：

`Begin WU-DC-CORE-01 only after GPT independently verifies the approved implementation-plan publication; no later Data Collection work unit is authorized yet.`

不要把项目设为 `COMPLETE`。Publication 完成后立即停止。

## Hard Stop for This Work Unit

本 Work Unit 严禁：

- 创建 `src/`。
- 创建 `pyproject.toml`。
- 安装 FastAPI、SQLAlchemy 或任何 dependency。
- 创建 migration、database schema、`tests/`、页面或业务 UI。
- 开始 `WU-DC-CORE-01`、任何 Collector、真实网站采集或第三方金融登录。

## Return to GPT

完成后返回以下可独立核验事实：

1. Work Commit W SHA。
2. Publication Commit P SHA。
3. P parent SHA。
4. live observed `origin/main` SHA。
5. `git status --short`。
6. final STATE：`state`、`revision`、`sync_status`、`active_work_unit`、`blockers`、`next_action`。
7. plan path。
8. plan status。
9. placeholder scan result。
10. plan self-review result。
11. `validate_project.py` exact output。
12. changed files in W。
13. changed files in P。
14. continuity resume result。
15. deviations / blockers。
16. 明确确认：no src created、no tests created、no database schema created、no migration created、no UI implementation、no dependency installed、`WU-DC-CORE-01` NOT started。

Completion Gate: `GPT_DECISION`。

# Data Collection 模块设计规范 — v1

状态：`DATA_COLLECTION_DESIGN_APPROVED`
--------------------------------------------------

日期：2026-09-12

项目：
PRJ-ASSET-MGMT-20260912-001

PROJECT_CONTEXT_ID：
43e85b1a-131b-4897-aa89-9b250d59fde0

上位架构：
docs/superpowers/specs/2026-09-12-asset-management-architecture-design.md

## 1. 模块职责

Data Collection 是唯一允许外部数据进入系统的业务模块。

负责：

- 用户手工输入；
- 用户月度账户确认；
- 用户主动提供的文件；
- 经批准的公开市场来源；
- Raw Evidence；
- Parser / Normalizer；
- Data Quality；
- Freshness；
- Reconciliation；
- Canonical Snapshot；
- Versioned Contract Publication。

不负责：

- 正式 Portfolio Ledger 计算；
- P&L；
- YTM；
- Duration；
- Convexity；
- DV01；
- Asset Allocation；
- Risk；
- Strategy；
- Rebalance；
- Trading。

## 2. 安全边界

系统和 AI/Codex 永远不得：

- 登录农业银行；
- 登录基金平台；
- 登录券商；
- 保存账号密码；
- 保存验证码；
- 保存 Cookie；
- 保存账户 Token；
- 自动交易；
- 自动申购；
- 自动赎回。

真实账户事实只能来自：

1. 用户人工确认；
2. 用户主动提供的账户文件。

公开市场数据不能覆盖账户事实。

## 3. Data Source Policy

所有来源必须属于：

AUTO_ALLOWED
MANUAL_DOWNLOAD
MANUAL_INPUT
DISABLED

公开可访问不代表允许长期自动抓取。

只有完成 Source Permission Audit 后才可升级 AUTO_ALLOWED。

未经批准的来源不得自动成为备用源。

## 4. Data Collection 组件

v1 包含：

Source Registry
Tracked Instrument Registry
Investment Plan Registry
Collector Adapter
Manual Import
Raw Evidence Store
Parser / Normalizer
Data Quality Gate
Freshness Gate
Reconciliation Gate
Canonical Snapshot Builder
Outbox / Contract Publisher

只有 Collector Adapter 可以访问经批准的外部网络。

其他业务计算模块禁止临时访问网页。

## 5. Raw Evidence

重要输入必须保留：

source_id
source_document_id
source_location
collected_at
content_hash
raw_evidence_ref
parser_version

解析结果不能成为唯一证据。

必须支持未来使用保存的 Raw Evidence 重新解析。

## 6. 债券范围

v1 只支持：

- 国债；
- 国家开发银行债券；
- 地方政府债。

v1 不建设信用评级采集和评级历史系统。

债券重点：

- 利率风险；
- Duration；
- DV01；
- Convexity；
- 期限结构；
- 流动性；
- 集中度；
- 到期现金流；
- 农业银行交易渠道可用性。

## 7. 债券 Authority

农业银行账户事实：
回答用户实际拥有什么。

公共市场基础设施：
回答债券是什么、市场如何参考估值。

农业银行公开报价：
回答当天公开为哪些债券提供客户报价。

永久区分：

market_reference_price
bank_execution_quote
actual_transaction_price

不得合并为一个 price。

## 8. 债券数据源

CBOND_VALUATION
- 初始 policy = MANUAL_DOWNLOAD
- candidate_for_auto = YES

CBOND_YIELD_CURVE
- 初始 policy = MANUAL_DOWNLOAD
- candidate_for_auto = YES

CHINAMONEY_BOND_MASTER
- 初始 policy = MANUAL_DOWNLOAD
- candidate_for_auto = YES

ABC_BOND_PRODUCT_UNIVERSE
- 初始 policy = MANUAL_DOWNLOAD
- candidate_for_auto = YES

ABC_DAILY_QUOTES
- 初始 policy = MANUAL_DOWNLOAD
- candidate_for_auto = YES

ABC_RISK_LEVEL
- OPTIONAL
- 若没有无需登录且稳定的公开来源，直接 DISABLED
- 核心计算不得依赖它

ABC_ACCOUNT_STATEMENT
- MANUAL_DOWNLOAD
- 禁止自动账户访问

## 9. ABC 当日公开报价债券池

生成：

ABCDailyTradableUniverseSnapshot.v1

必须区分：

BUY_QUOTED
SELL_QUOTED
TWO_WAY_QUOTED
NO_CURRENT_QUOTE

记录：

can_customer_buy
can_customer_sell

不得声明：
GUARANTEED_TRADABLE

农行公开报价不等于保证用户最终成交。

理论 Strategy Universe 与 ABC Execution Candidate Universe 必须分离。

## 10. 当前基金跟踪范围

不建设全市场基金数据库。

只跟踪：

- 当前实际持有；
- 用户明确加入观察列表。

当前代码：

019172
017641
016452
021707
000307
020602
161130
161125
002963

基金名称和分类不得根据代码猜测，必须由 Instrument Registry 验证。

## 11. Market Return 与 Personal Return 分离

永久区分：

Market Return
Personal Holding Return

市场涨跌不能直接等同个人收益。

## 12. 基金/ETF 数据语义

永久区分：

MARKET_CLOSE_PRICE
OFFICIAL_NAV
IOPV
UNDERLYING_INDEX_LEVEL

数值不同本身不是 Data Conflict。

黄金基金/ETF 的正式账户估值使用用户实际持有产品的对应估值来源。

黄金基准只能用于：

- 市场解释；
- 异常检查；
- tracking 分析。

## 13. Investment Plan 页面

必须提供独立：

基金定投设置

允许：

- 启用；
- 暂停；
- 修改定投方式；
- 修改金额；
- 指定 effective date；
- 查看历史版本；
- 显示预计本月投入。

v1 schedule type：

NONE
DAILY
TRADING_DAY
WEEKLY
MONTHLY

暂不实现智能定投。

## 14. 当前 Investment Plan Baseline

019172:
TRADING_DAY
10 RMB
ENABLED

017641:
TRADING_DAY
10 RMB
ENABLED

016452:
DAILY
40 RMB
ENABLED

021707:
DAILY
10 RMB
ENABLED

000307:
DAILY
10 RMB
ENABLED

020602:
TRADING_DAY
10 RMB
ENABLED

161130:
NONE
0 RMB
HELD_ONLY

161125:
NONE
0 RMB
HELD_ONLY

002963:
NONE
0 RMB
HELD_ONLY

DAILY 不得擅自解释为 TRADING_DAY。

必须按实际产品申购日历处理非交易日行为。

## 15. Investment Plan Versioning

计划修改必须按 effective date 创建新版本。

禁止重写旧版本。

暂停也是新版本。

历史规则必须永久可重放。

## 16. 计划不等于 Account Fact

允许状态：

PLANNED
EXPECTED
PENDING_CONFIRMATION
PROVISIONAL

Investment Plan 永远不能自己生成 CONFIRMED units。

真实 confirmed units 只能由账户事实确认。

## 17. 份额确认滞后

必须支持：

pending_amount
pending_units
estimated_units
confirmed_units

允许：

PENDING_AMOUNT_ONLY
PENDING_UNITS_KNOWN

estimated_units 永远不能自动升级为 confirmed_units。

必须支持海外/QDII基金非当日确认份额。

## 18. 月度账户确认

用户不需要每日提供交易记录。

每个月执行一次人工账户确认。

优先选择中国市场非交易日。

默认：

FIRST_CN_NON_TRADING_DAY_AFTER_MONTH_END

必须分别保存：

snapshot_as_of_date
confirmed_at

用户在周末确认，不代表市场数据属于周末。

## 19. 月度必填字段

每只基金必须确认：

instrument_code
account_value
confirmed_units
snapshot_as_of_date

confirmed_units 为必填。

条件字段：

pending_amount
pending_units

若平台只显示其中一种，另一种允许 UNKNOWN。

## 20. MonthlyAccountAnchor.v1

每次月度确认生成：

anchor_id
instrument_code
snapshot_as_of_date
confirmed_at
confirmed_units
account_value
pending_amount
pending_units
source = MANUAL_MONTHLY_CONFIRMATION
quality_status
reconciliation_status

新的 Anchor 是下一个周期估算的起点。

## 21. Confirmed 与 Estimated 永久分离

所有账户相关值必须有确认等级。

例如：

confirmed_units
estimated_units
confirmed_account_value
estimated_account_value

UI 必须显示：

最近账户确认日期
最近确认资产
当前估算资产
当前待确认金额/份额

## 22. Data Quality Gate

状态：

VERIFIED
VALID
SUSPECT
CONFLICT
INVALID
QUARANTINED

至少检查：

格式
日期
数值范围
Instrument Identity
业务一致性
时间连续性
重复数据
同语义来源交叉验证

异常值不得自动删除。

SUSPECT / CONFLICT 必须隔离。

不同语义来源不得被错误认定为 conflict。

例如：

ABC customer quote
与
ChinaBond reference valuation

本来就可能不同。

## 23. Freshness Gate

状态：

FRESH
STALE
EXPIRED
UNKNOWN
MISSING

Freshness 必须基于：

- 数据类型；
- 市场交易日历；
- 发布日历；
- 数据源更新周期。

禁止仅使用：

now - collected_at

判断 freshness。

## 24. Market Time Semantics

至少保存：

as_of_time
published_at
collected_at
effective_at

如果来源只提供日期：

不得声明 REALTIME。

ETF 周五收盘价格在周六仍可作为最新已结束交易日的 FRESH 数据。

## 25. QDII / 海外基金时间对齐

支持：

pricing_market
market_timezone
trade_date
nav_date
underlying_market_date

状态：

ALIGNED
PARTIALLY_ALIGNED
MISALIGNED
UNKNOWN

跨市场时间差不自动等于 Data Error。

## 26. Reconciliation Gate

状态：

RECONCILED
MINOR_DIFFERENCE
MATERIAL_DIFFERENCE
UNRESOLVED

至少比较：

confirmed_units
pending_amount
pending_units
account_value
planned contribution
estimated position

阈值必须可配置。

用户月度确认 Authority 高于系统估算。

发生差异：

禁止修改历史交易。

允许创建 Reconciliation Adjustment，
并从新的真实 Anchor 开始下一周期。

## 27. Data Authority Policy

Account Fact：

1. 用户月度账户确认
2. 用户主动提供的正式账户文件
3. 系统估算

Market Fact：

1. 官方交易所/官方市场基础设施
2. 基金管理人正式披露
3. 经批准辅助来源

Bond：

actual transaction
→ 用户/农行账户事实

ABC quote
→ ABC Daily Quote

market valuation
→ ChinaBond reference

bond terms
→ 官方发行/上市资料

不得根据“哪个数字看起来更合理”动态改变 Authority。

## 28. Canonical Snapshot

正式计算禁止实时临时访问网站。

必须先生成固定 Snapshot。

至少：

market_snapshot_id
account_snapshot_id
plan_snapshot_id

Snapshot 可追踪：

Raw Evidence
Parser version
quality_status
freshness_status
reconciliation_status
source provenance

Portfolio、Valuation、Risk、Bond Strategy、Rebalance、Reporting 只消费 Snapshot/版本化 contract。

## 29. 核心输出契约

至少：

ValidatedMarketObservation.v1
AccountImportEnvelope.v1
InvestmentPlanSnapshot.v1
MonthlyAccountAnchor.v1
ABCDailyTradableUniverseSnapshot.v1
CollectionRunStatus.v1
DataQualityAlert.v1

AccountImportEnvelope 不得直接修改 Portfolio Ledger。

## 30. 模块隔离

下游模块不得直接读取 Data Collection 内部表。

只允许版本化 contract / canonical snapshot。

Collector Adapter 可以替换，而下游业务模块不应跟着修改。

## 31. 失败与降级

采集失败：

禁止把旧数据重新标 FRESH。

允许：

- 上一有效数据 + STALE；
- 已批准备用源；
- MANUAL_DOWNLOAD；
- MANUAL_INPUT。

未经批准的新源不得自动接管。

Quality：

SUSPECT → Quarantine
CONFLICT → Quarantine
INVALID → Reject
STALE → 保存，但是否允许使用由下游规则决定

## 32. NOT_EVALUATED 规则

所有下游算法必须声明 Required Data。

数据不足时返回：

NOT_EVALUATED

原因例如：

MISSING_MARKET_DATA
STALE_ACCOUNT_DATA
UNRESOLVED_RECONCILIATION
MISSING_QUOTE

数据不足不得解释为：
NOT_RECOMMENDED

## 33. Portfolio Confidence

状态：

CONFIRMED
MOSTLY_CONFIRMED
ESTIMATED
INSUFFICIENT

少量近期未确认定投：
MOSTLY_CONFIRMED

长期未月度确认或重大 unresolved reconciliation：
INSUFFICIENT

INSUFFICIENT 时：
REBALANCE_NOT_EVALUATED

## 34. 调度

日常：

- 经批准市场数据采集；
- Quality Gate；
- Freshness Gate；
- Market Snapshot。

定投日：

- 根据当前 Plan Version 生成 Planned / Expected contribution；
- 不自动确认份额。

月度非交易日：

- 提醒用户确认；
- 每只基金填写 account value；
- 必填 confirmed units；
- 填写 pending amount / pending units；
- Reconciliation；
- 新 MonthlyAccountAnchor。

## 35. UI v1

基金定投设置页：

- tracked funds；
- enable/pause；
- schedule；
- amount；
- effective date；
- plan history；
- expected monthly contribution。

月度账户确认页：

自动列出所有持有基金。

显示：

- 系统预计投入；
- 上月 Anchor；
- 当前 Pending 状态。

输入：

- account value；
- confirmed units；
- pending amount；
- pending units；
- snapshot business date。

输出：

- reconciliation status；
- difference；
- new Anchor。

## 36. v1 Explicit Non-Goals

不做：

- 金融账户自动登录；
- 交易 API；
- 自动交易；
- 自动申购赎回；
- AI 自动确认真实持仓；
- 全市场基金数据库；
- 全市场债券信用评级；
- 商业债信用分析；
- 黑箱 AI 投资判断；
- 复杂智能定投；
- 未通过 Source Permission Audit 的生产自动抓取；
- Kafka。

## 37. Acceptance Criteria

至少证明：

1. 每条正式数据都有 source 和 time；
2. Raw Evidence 可追踪；
3. Quality/Freshness 独立；
4. STALE 不会伪装 FRESH；
5. SUSPECT 不会进入正式计算；
6. ESTIMATED 不会伪装 Account Fact；
7. Investment Plan 可以 version；
8. 修改 plan 不重写历史；
9. 当前 9 个基金可配置；
10. 月度 confirmed_units 必填；
11. pending amount/units 均可表达；
12. 海外/QDII支持确认时差；
13. Monthly Anchor 可校准估算；
14. ABC 当日公开报价池独立 Snapshot；
15. 债券 v1 限于国债、国开债、地方债；
16. market reference / ABC quote / actual transaction 不混淆；
17. Adapter 可替换而下游不修改；
18. 所有计算可绑定 Snapshot 重现；
19. 数据不足返回 NOT_EVALUATED；
20. 无 Codex、无 AI、无金融账户登录时，确定性生产系统可独立运行。

## 38. Implementation Gate

本规范已获得用户明确批准。

下一阶段只允许：

- implementation planning；
- contract schema design；
- database model design；
- Source Permission Audit design；
- test plan。

在实施计划再次获得批准之前：

禁止业务代码实现。

--------------------------------------------------
END OF APPROVED SPEC

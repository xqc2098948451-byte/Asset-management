# 个人资产配置与债券策略管理系统 — v1 架构基线

- 日期：2026-09-12
- 状态：ARCHITECTURE_BASELINE_APPROVED
- 目标路径：`project/docs/superpowers/specs/2026-09-12-asset-management-architecture-design.md`
- 框架基线：GPT–Codex Framework v2.2.1

## 1. 项目定位

本项目是部署在腾讯云上的个人资产配置与债券策略管理系统。

系统目标：

1. 收集并保存用户主动提供的账户事实；
2. 从允许使用的公开来源采集市场事实；
3. 对股票基金、单只债券、黄金 ETF、现金进行统一估值；
4. 自动计算资产配置、偏离度、债券风险与策略适配度；
5. 自动生成风险提示、再平衡建议和周期性报告；
6. 所有交易决策和实际交易均由用户人工完成。

系统不是自动交易系统，不是银行核心系统，不是券商账户聚合系统，也不是高频交易系统。

## 2. 已确认的硬约束

### 2.1 金融账户与交易

- 不登录农业银行、券商、基金平台或其他金融账户。
- 不保存金融账户密码、短信验证码、Cookie、Token 或其他登录凭证。
- 不调用银行 API、券商 API、交易 API。
- 不自动下单、不自动买卖、不自动调仓。
- 系统只产生分析、预警和建议。
- 最终交易由用户人工执行。

### 2.2 市场数据

- 业务系统不依赖第三方商业数据 API。
- 市场数据优先来自允许使用的官方公开页面、公开下载文件或用户主动导入文件。
- 若来源不适合自动机器采集，则降级为人工下载/上传或手工录入。
- “网页可见”不自动等同于“允许长期程序化采集”。
- 每个数据源必须在 `DATA_SOURCE_POLICY` 中标记采集级别：
  - `AUTO_ALLOWED`
  - `MANUAL_DOWNLOAD`
  - `MANUAL_INPUT`
  - `DISABLED`

### 2.3 Codex

- Codex 不属于生产运行链路。
- 腾讯云上的资产管理系统必须在 Codex 不运行时独立工作。
- 用户每周从桌面版 Codex 人工触发一次维护工作。
- Codex 只负责代码维护、采集器修复、测试、升级和部署。
- Codex 不参与日常投资计算，不登录金融账户，不执行交易。
- Codex 的开发治理受 GPT–Codex Framework 约束。

## 3. 当前资产范围

第一阶段覆盖：

### 3.1 股票基金

- 纳斯达克指数相关基金/ETF
- 标普 500 指数相关基金/ETF
- 中国低波红利指数相关基金/ETF

### 3.2 债券

- 通过农业银行“债市宝”持有的单只债券
- 单券级持仓、现金流、估值、利率风险、信用风险与策略管理

### 3.3 黄金

- 境内黄金 ETF
- 可保留国内黄金基准价格作为参考市场事实

### 3.4 现金

- 用户提供的现金余额
- 后续可区分一级现金与二级流动性储备

## 4. 总体架构原则

### 4.1 模块化单体优先

第一版采用：

- 模块化单体业务核心
- 独立后台 Worker
- PostgreSQL
- PostgreSQL 分 Schema
- 版本化内部契约
- 事务 Outbox / 事件机制
- 可替换 Adapter
- 腾讯云部署

暂不采用完整微服务架构。

原因：

- 当前为单用户/小规模投资系统；
- 业务领域仍在逐步细化；
- 过早微服务化会增加部署、网络、事务和调试复杂度；
- 模块可替换性通过契约和边界实现，而不是靠“每个模块必须是独立服务”。

### 4.2 模块可替换原则

最高级别架构约束：

> 任何业务模块都不得成为另一个业务模块的内部实现依赖；跨模块只允许使用版本化契约。

禁止：

- 模块 A 直接读取模块 B 的内部表；
- 模块 A 调用模块 B 的内部函数；
- 模块之间共享可变内部模型；
- 为方便而跨 Schema JOIN 内部表。

允许：

- 使用稳定的版本化输入/输出契约；
- 使用模块发布的标准事件；
- 使用明确的只读投影/公共视图；
- 使用 Adapter 替换外部数据来源。

### 4.3 端口 / 适配器

每个模块分为：

- Domain/Core：业务规则与确定性计算
- Port：模块对外定义的输入/输出契约
- Adapter：数据库、公开网页、文件导入、定时任务、UI 等实现

替换 Adapter 不得改变 Domain/Core。

## 5. 六层业务架构

### 5.1 数据入口层

负责：

- 官方公开市场数据采集
- 用户上传 Excel/CSV/PDF/截图
- 手工录入
- 原始文件归档

### 5.2 核心数据层

核心是 `Portfolio Ledger`。

回答：

> 用户实际上拥有什么？

记录：

- 资产
- 持仓
- 数量
- 买入成本
- 买入日期
- 交易历史
- 票息
- 本金兑付
- 现金流

账户事实只能由用户输入/导入的证据改变。

### 5.3 计算层

负责确定性计算：

- 资产估值
- 组合快照
- 资产权重
- 资产偏离
- YTM
- Macaulay Duration
- Modified Duration
- Convexity
- DV01
- 债券现金流
- 到期结构
- 压力测试

核心投资计算不得依赖大模型。

同一输入和同一算法版本必须产生同一结果。

### 5.4 风险层

包括：

- Portfolio Risk
- Allocation Risk
- Bond Risk
- Data Risk

统一风险状态：

- `GREEN`
- `YELLOW`
- `RED`

同时支持数据状态：

- `FRESH`
- `PARTIALLY_STALE`
- `STALE`
- `QUARANTINED`

### 5.5 决策层

包括：

- Asset Allocation
- Bond Strategy
- Rebalance

仅产生建议，不执行交易。

### 5.6 展示与报告层

包括：

- Dashboard
- Weekly Report
- Alerts
- 历史资产曲线
- 历史风险变化
- 再平衡建议

报告核心由确定性数据 + 规则 + 模板生成。

## 6. 九个主要业务模块

### 6.1 Data Collection

职责：

- 获取允许自动获取的公开数据；
- 接收用户上传文件；
- 保存原始数据；
- 标记来源、时间和采集方式。

不负责投资计算。

### 6.2 Portfolio Ledger

职责：

- 保存账户事实；
- 保存真实持仓、成本、交易和现金流；
- 作为账户数据 Source of Truth。

### 6.3 Market Data & Valuation

职责：

- 保存市场事实；
- 将持仓与市场价格对应；
- 生成资产和组合估值快照。

### 6.4 Asset Allocation

职责：

- 管理战略资产配置；
- 计算股票/债券/黄金/现金实际权重；
- 计算目标权重与实际权重偏离。

### 6.5 Bond Management

独立债券子系统，包括：

- Bond Master
- Bond Position
- Bond Cash Flow
- Bond Valuation
- Yield Curve
- Interest Rate Risk
- Credit Risk
- Liquidity Risk
- Concentration Risk
- Maturity Structure
- Bond Strategy Classification
- Strategy Monitor

### 6.6 Risk Engine

统一组合层风险。

负责聚合：

- 资产配置偏离
- 债券利率风险
- 债券信用风险
- 集中度风险
- 到期风险
- 数据风险

### 6.7 Rebalancing

负责：

- 识别资产偏离；
- 生成再平衡建议；
- 优先使用新增资金、票息和自然到期资金；
- 必要时才提示考虑出售资产。

不执行交易。

### 6.8 Reporting

负责：

- Dashboard
- 周报
- 风险提示
- 策略状态
- 数据新鲜度状态
- 计算版本与来源追踪

### 6.9 Operations & Maintenance

负责：

- 定时任务
- 健康检查
- 日志
- 监控
- 备份
- 恢复
- 部署
- Codex 每周维护入口

## 7. 债券模块总体定位

债券不能只作为“资产配置中的一个百分比”。

它需要同时回答：

1. 这是什么债券？
2. 当前值多少钱？
3. 有什么风险？
4. 为什么持有它？
5. 原持有逻辑是否仍然有效？

### 7.1 债券基础分类

示例：

- 国债
- 政策性金融债
- 地方政府债
- 金融债
- 企业债
- 公司债
- 其他

### 7.2 第一阶段债券策略

第一阶段策略池：

- `HTM` — 持有至到期
- `RIDE` — 收益率曲线骑乘
- `CARRY` — Carry 收益策略
- `LADDER` — 债券梯形
- `LIQUIDITY_RESERVE` — 流动性储备

`BARBELL` 第一阶段作为组合分析能力存在，不作为主要单券策略标签。

### 7.3 策略分类原则

策略分类不采用不可解释的黑箱。

每只债券可以拥有多个策略适合度评分，例如：

- HTM: 92
- LADDER: 86
- CARRY: 81
- RIDE: 74

每个评分必须提供：

- 输入数据
- 规则版本
- 得分构成
- 扣分原因
- 数据缺失情况
- 失效条件

区分：

- `ELIGIBLE`
- `NOT_RECOMMENDED`
- `NOT_EVALUATED`

“数据不足”不能等同于“不推荐”。

## 8. 数据事实分层

必须分开保存：

### 8.1 Account Fact

用户真实投资事实：

- 买入日期
- 买入价格
- 数量/面值
- 实际成本
- 票息到账
- 本金兑付
- 现金余额

只能由用户导入/确认数据改变。

### 8.2 Market Fact

公开市场事实：

- 基金净值
- ETF 收盘价
- 黄金参考价
- 债券参考估值
- 收益率曲线
- 公开评级/隐含评级

市场事实不能修改账户事实。

### 8.3 Calculated Fact

系统计算结果：

- 组合市值
- 权重
- 偏离度
- YTM
- Duration
- DV01
- Risk Score
- Strategy Score

必须记录所使用的数据快照和模型版本。

## 9. Data Vault & Provenance

所有重要数据必须可追溯。

原始目录逻辑：

```text
data/
├── raw/
│   ├── funds/
│   ├── bonds/
│   ├── gold/
│   └── account-imports/
├── normalized/
└── rejected/
```

每条关键市场记录至少保存：

- source
- source_document
- as_of_date
- published_at（如可得）
- collected_at
- checksum
- parser_version
- freshness_status

目标：

> 数据库里的关键数字必须能够回答“它从哪里来的？”

## 10. Data Quality Gate

公开数据不得直接进入投资计算。

流程：

```text
Raw
  ↓
格式校验
  ↓
日期校验
  ↓
完整性校验
  ↓
重复校验
  ↓
异常值校验
  ↓
来源策略校验
  ↓
PASS / QUARANTINE
```

异常数据进入隔离区。

若当日数据不可用：

- 使用上一有效值时必须明确标记 `STALE`；
- 不得将旧值伪装为新值；
- 超过模块允许的 stale 阈值时必须阻止相关决策结果升级为正常状态。

## 11. Valuation Calendar

不同资产市场日期可能不同。

所有市场事实必须带：

- `as_of_date`
- `published_at`
- `collected_at`
- `freshness_status`

组合快照必须标记：

- `FULLY_ALIGNED`
- `PARTIALLY_STALE`
- `STALE`

QDII 基金、境内 ETF、债券估值和黄金可能使用不同有效日期，系统不得因此制造虚假的资产偏离。

## 12. 内部事件与 Outbox

模块之间优先通过版本化事件通信。

示例：

- `MarketDataUpdated.v1`
- `ValuationCompleted.v1`
- `PortfolioSnapshotCreated.v1`
- `BondAnalyticsCompleted.v1`
- `RiskCalculationCompleted.v1`
- `RebalanceAssessmentCompleted.v1`
- `WeeklyReportGenerated.v1`

第一版不引入 Kafka。

采用：

- PostgreSQL Outbox
- 后台 Worker
- 幂等消费者

目标：

- 数据更新与事件发布保持一致；
- 重复执行不得产生重复业务结果；
- 模块可独立重跑。

## 13. Job Orchestration

生产系统自动运行：

```text
Market Collection
      ↓
Data Validation
      ↓
Normalization
      ↓
Valuation
      ↓
Portfolio Snapshot
      ↓
Bond Analytics
      ↓
Risk Engine
      ↓
Rebalance Engine
      ↓
Reporting
```

每个 Job 状态：

- `PENDING`
- `RUNNING`
- `SUCCESS`
- `FAILED`
- `SKIPPED`
- `DEGRADED`

必须支持：

- retry
- resume
- idempotent rerun

若上游关键数据失败，下游必须根据规则：

- 停止；
- 降级；
- 使用上一次有效快照并标记 stale。

不得静默继续。

## 14. 模型、规则和策略版本

以下全部版本化：

- Allocation Strategy
- Bond Strategy Rules
- Risk Rules
- Valuation Models
- Data Parsers

每个计算结果必须记录：

- input_snapshot_id
- market_snapshot_id
- strategy_version
- risk_rule_version
- valuation_model_version
- calculated_at

历史报告必须可以解释当时使用的是哪一版规则。

## 15. 模块替换机制

模块升级必须支持旧版与新版并行验证。

流程：

```text
V1 Production
      +
V2 Shadow
      ↓
相同输入
      ↓
结果比较
      ↓
契约测试
      ↓
业务验收
      ↓
切换 V2
      ↓
保留 V1 回滚窗口
```

禁止未经 shadow/验收直接删除生产旧模块。

每个模块必须具备：

- 单元测试
- 契约测试
- 集成测试
- 回归样本
- 模块级健康检查
- 回滚办法

## 16. 腾讯云运行架构

逻辑组件：

- Tencent Cloud CVM
- Web Application
- Background Worker
- PostgreSQL
- 原始文件存储
- 日志/监控
- 自动备份

生产运行不依赖 Codex。

Codex 维护路径：

```text
用户桌面版 Codex
      ↓
人工触发远程维护
      ↓
腾讯云项目
      ↓
检查 / 修复 / 测试 / 部署
```

## 17. 可观测性与恢复

系统必须具备：

- 应用健康状态
- Worker 状态
- Job 状态
- 数据新鲜度
- 数据采集失败
- 数据隔离数量
- 数据库状态
- 日志
- 关键错误告警

恢复能力包括：

- PostgreSQL 自动备份
- 原始文件备份
- 配置备份
- 模块版本回滚
- 数据库 Migration 回滚/恢复方案

## 18. 安全与治理原则

必须固化到 GPT–Codex Framework 项目治理中：

- 禁止自动交易
- 禁止金融账户登录
- 禁止保存金融账户凭证
- 禁止绕过数据源使用许可
- 禁止 AI 直接替代确定性金融计算
- 生产系统不得依赖 Codex
- 生产数据不得被开发任务任意删除
- 破坏性生产操作需要明确批准
- Framework Kernel / Built-ins 保持只读
- 项目是权威源，Framework 是辅助源

## 19. 开发方法

项目采用严格的模块递进开发。

每个模块流程：

1. 讨论模块目的；
2. 冻结职责；
3. 冻结边界；
4. 确定数据来源；
5. 定义输入契约；
6. 定义输出契约；
7. 定义失败/降级；
8. 定义安全约束；
9. 定义验收标准；
10. 用户批准；
11. 创建对应 Codex Work Unit；
12. Codex 按测试驱动方式开发；
13. 单元测试；
14. 契约测试；
15. 集成测试；
16. 用户/系统验收；
17. 进入生产；
18. 再开始讨论下一模块。

未验收的模块不得作为下一个模块的隐式实现依赖。

## 20. 推荐模块开发顺序

第一阶段按以下顺序：

1. Data Collection
2. Portfolio Ledger
3. Market Data & Valuation
4. Asset Allocation
5. Bond Management
6. Risk Engine
7. Rebalancing
8. Reporting
9. Operations / Production Hardening

原因：

- 数据先于算法；
- 账户事实先于市场估值；
- 估值先于资产配置；
- 基础资产模型稳定后再进入复杂债券模块；
- 风险与再平衡依赖上游模块标准化输出；
- 报告最后消费稳定契约。

## 21. v1 架构基线冻结范围

本规范冻结的是：

- 系统目标
- 安全边界
- 总体模块
- 模块隔离原则
- 数据事实分层
- 数据质量原则
- 自动任务原则
- 版本化原则
- 替换/回滚原则
- 腾讯云运行边界
- Codex 职责边界
- 模块递进开发流程

本规范明确不冻结：

- Data Collection 的具体网站和文件格式
- 数据库表字段
- UI 详细设计
- 具体资产配置比例
- 具体风险阈值
- 债券策略评分公式
- 具体调度时间
- 具体腾讯云实例规格

这些内容在对应模块细化阶段逐个确定。

## 22. 下一步

下一模块：

`Data Collection`

其设计必须先解决：

- 数据源清单
- 每个数据源的合法/技术可采集性
- 自动 / 人工采集分级
- 原始证据格式
- 数据新鲜度
- Parser 隔离
- Data Quality Gate
- 数据源失效时的降级
- 模块输入/输出契约
- 验收测试

在 Data Collection 设计得到用户批准后，才创建第一个正式业务 Codex Work Unit 开发该模块。

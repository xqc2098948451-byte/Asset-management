# Project

## Identity

- Project ID: `PRJ-ASSET-MGMT-20260912-001`
- Project Context ID: `43e85b1a-131b-4897-aa89-9b250d59fde0`
- Name: Asset-management
- Purpose: Personal asset allocation and single-bond strategy/risk management system deployed on Tencent Cloud.

## Evidence-derived project profile

- Repository: `xqc2098948451-byte/Asset-management`
- GitHub repository ID: `1366683980`
- Default branch: `main`
- Repository state at bootstrap: empty new repository
- Framework: GPT–Codex Framework v2.2.1
- Asset scope: equity index funds/ETFs, individual bonds held through ABC Bond Market Treasure, gold ETF, and cash.
- Deployment intent: Tencent Cloud.
- Financial account access: prohibited.
- Automatic trading: prohibited.
- External bank/broker/trading APIs: prohibited.
- Market data: official public sources/files when allowed, otherwise user-provided files/manual input.
- Core financial calculations: deterministic and reproducible; not delegated to an LLM.

## Architecture and constraints

- Modular monolith first, with independently replaceable modules.
- Cross-module access is only through versioned contracts/events/public projections; modules must not depend on another module's internal tables or functions.
- PostgreSQL may be shared physically but is logically separated by module/schema ownership.
- Production operation is independent of Codex.
- Codex is used only for user-triggered development, maintenance, testing, and deployment.
- The approved architecture baseline is `docs/superpowers/specs/2026-09-12-asset-management-architecture-design.md`.
- No business module implementation is authorized by this bootstrap step.

## Governance rationale

Bootstrap phase two establishes only project identity, GitHub continuity metadata, the required cross-project context guardrail, initial proposed state, and the approved architecture baseline. Other Built-ins remain unselected until the separate governance-completion work unit evaluates reuse and validation requirements.

## Source-of-truth rule

- This file explains **what the project is**.
- `CONTROL.json` defines **which governance extensions are enabled**.
- `STATE.json` defines **where governed execution is now**.

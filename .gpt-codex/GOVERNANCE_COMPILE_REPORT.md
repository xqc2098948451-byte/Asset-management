# Governance Compile Report

- Project ID: `PRJ-ASSET-MGMT-20260912-001`
- Work Unit: `WORK-GOVERNANCE-BOOTSTRAP-001`
- Kernel Version: `2.0.0`
- Framework Version: `2.2.1`
- Base Commit: `6ec7850454f0e6e0cd8805c9baff4abfc246e1ea`
- Compatibility Result: `NO_ACTION`

## Compile Checks

- CONTROL Schema: PASS
- STATE Schema: PASS
- Extension IDs unique: PASS
- Referenced extensions exist: PASS
- Permissions narrow correctly: PASS
- Project-local provenance complete: PASS (no project-local extensions)
- Harvest namespace valid: PASS
- State/revision valid: PASS (`AUTHORIZED@revision-1`)
- Required capability availability: PASS
- Project context binding: PASS

## Validator Evidence

Actual command:

```text
python D:\资产管理\_gpt-codex-framework-readonly\.gpt-codex\scripts\validate_project.py .
```

Initial pre-authorization run:

```text
RESULT: PASS
PROJECT: PRJ-ASSET-MGMT-20260912-001
STATE: PROPOSED@revision-0
PROJECT_CONTEXT_BINDING: PASS
```

Post-authorization run:

```text
RESULT: PASS
PROJECT: PRJ-ASSET-MGMT-20260912-001
STATE: AUTHORIZED@revision-1
PROJECT_CONTEXT_BINDING: PASS
```

## Result

`PASS`

## Blocking reasons

None.

## Scope Confirmation

The selected Built-ins are Framework snapshots copied under
`.gpt-codex/extensions/`. No project-local Skill, Guardrail, or Fitness was
created. `test-suite-pass` and `build-pass` remain disabled because this
repository has no business code, test suite, or build system. Data Collection
was not started.

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)

SCHEMA = "data_collection"
metadata = MetaData(schema=SCHEMA)
financial_type = Numeric(28, 10)


Table(
    "data_source",
    metadata,
    Column("source_id", String(64), primary_key=True),
    Column("source_code", String(64), nullable=False),
    Column("policy", String(32), nullable=False),
    Column("display_name", String(128), nullable=True),
    UniqueConstraint("source_code", name="uq_data_source_source_code"),
)

Table(
    "tracked_instrument",
    metadata,
    Column("instrument_id", String(64), primary_key=True),
    Column("instrument_code", String(32), nullable=False),
    Column("verification_status", String(32), nullable=False),
    Column("fund_name", String(256), nullable=True),
    Column("category", String(128), nullable=True),
    Column("benchmark", String(256), nullable=True),
    UniqueConstraint("instrument_code", name="uq_tracked_instrument_code"),
)

Table(
    "market_calendar_day",
    metadata,
    Column("calendar_code", String(64), primary_key=True),
    Column("calendar_date", Date, primary_key=True),
    Column("is_trading_day", Boolean, nullable=False),
)

Table(
    "investment_plan_version",
    metadata,
    Column("plan_version_id", String(64), primary_key=True),
    Column("instrument_code", String(32), nullable=False),
    Column("schedule_type", String(32), nullable=False),
    Column("amount", financial_type, nullable=False),
    Column("status", String(32), nullable=False),
    Column("effective_from", Date, nullable=False),
    Column("effective_to", Date, nullable=True),
    CheckConstraint("amount >= 0", name="ck_investment_plan_amount_non_negative"),
    UniqueConstraint(
        "instrument_code", "effective_from", name="uq_investment_plan_effective_start"
    ),
)

Table(
    "planned_contribution",
    metadata,
    Column("contribution_id", String(64), primary_key=True),
    Column("instrument_code", String(32), nullable=False),
    Column("plan_version_id", String(64), nullable=False),
    Column("contribution_date", Date, nullable=False),
    Column("investment_amount", financial_type, nullable=False),
    Column("estimated_units", financial_type, nullable=True),
    Column("confirmed_units", financial_type, nullable=True),
    Column("status", String(32), nullable=False),
    CheckConstraint(
        "investment_amount >= 0", name="ck_planned_contribution_amount_non_negative"
    ),
    CheckConstraint(
        "estimated_units IS NULL OR estimated_units >= 0",
        name="ck_planned_contribution_estimated_units_non_negative",
    ),
    CheckConstraint(
        "confirmed_units IS NULL OR confirmed_units >= 0",
        name="ck_planned_contribution_confirmed_units_non_negative",
    ),
    UniqueConstraint(
        "instrument_code", "plan_version_id", "contribution_date",
        name="uq_planned_contribution_identity",
    ),
)

Table(
    "raw_evidence",
    metadata,
    Column("evidence_id", String(64), primary_key=True),
    Column("content_sha256", String(64), nullable=False),
    Column("storage_uri", Text, nullable=False),
    Column("original_filename", String(512), nullable=True),
    Column("metadata", JSON, nullable=False),
    Column("collected_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("content_sha256", name="uq_raw_evidence_content_sha256"),
)

Table(
    "market_observation",
    metadata,
    Column("observation_id", String(64), primary_key=True),
    Column("instrument_code", String(32), nullable=False),
    Column("observation_type", String(64), nullable=False),
    Column("value", financial_type, nullable=False),
    Column("as_of_date", Date, nullable=False),
    Column("as_of_time", DateTime(timezone=True), nullable=True),
    Column("published_at", DateTime(timezone=True), nullable=True),
    Column("collected_at", DateTime(timezone=True), nullable=False),
    Column("effective_at", DateTime(timezone=True), nullable=True),
    Column("source_id", String(64), nullable=False),
    Column("quality_status", String(32), nullable=False),
    Column("freshness_status", String(32), nullable=False),
    CheckConstraint("value >= 0", name="ck_market_observation_value_non_negative"),
)

Table(
    "monthly_reconciliation_cycle",
    metadata,
    Column("cycle_id", String(64), primary_key=True),
    Column("period_month", Date, nullable=False),
    Column("preferred_confirmation_date", Date, nullable=False),
    Column("status", String(32), nullable=False),
    UniqueConstraint("period_month", name="uq_reconciliation_cycle_period_month"),
)

Table(
    "monthly_account_anchor",
    metadata,
    Column("anchor_id", String(64), primary_key=True),
    Column("instrument_code", String(32), nullable=False),
    Column("snapshot_as_of_date", Date, nullable=False),
    Column("confirmed_at", DateTime(timezone=True), nullable=False),
    Column("confirmed_units", financial_type, nullable=False),
    Column("account_value", financial_type, nullable=False),
    Column("pending_amount", financial_type, nullable=True),
    Column("pending_units", financial_type, nullable=True),
    Column("source", String(64), nullable=False),
    Column("quality_status", String(32), nullable=False),
    Column("reconciliation_status", String(32), nullable=False),
    CheckConstraint("confirmed_units >= 0", name="ck_anchor_confirmed_units_non_negative"),
    CheckConstraint("account_value >= 0", name="ck_anchor_account_value_non_negative"),
    CheckConstraint(
        "pending_amount IS NULL OR pending_amount >= 0",
        name="ck_anchor_pending_amount_non_negative",
    ),
    CheckConstraint(
        "pending_units IS NULL OR pending_units >= 0",
        name="ck_anchor_pending_units_non_negative",
    ),
)

Table(
    "reconciliation_adjustment",
    metadata,
    Column("adjustment_id", String(64), primary_key=True),
    Column("anchor_id", String(64), nullable=False),
    Column("instrument_code", String(32), nullable=False),
    Column("unit_difference", financial_type, nullable=False),
    Column("amount_difference", financial_type, nullable=False),
    Column("reason", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "canonical_snapshot",
    metadata,
    Column("snapshot_id", String(64), primary_key=True),
    Column("market_snapshot_id", String(64), nullable=True),
    Column("account_snapshot_id", String(64), nullable=True),
    Column("plan_snapshot_id", String(64), nullable=True),
    Column("as_of_date", Date, nullable=False),
    Column("source_provenance", JSON, nullable=False),
    Column("raw_evidence_id", String(64), nullable=True),
    Column("parser_version", String(64), nullable=True),
    Column("quality_status", String(32), nullable=False),
    Column("freshness_status", String(32), nullable=False),
    Column("reconciliation_status", String(32), nullable=False),
)

Table(
    "data_quality_alert",
    metadata,
    Column("alert_id", String(64), primary_key=True),
    Column("observation_id", String(64), nullable=True),
    Column("instrument_code", String(32), nullable=True),
    Column("quality_status", String(32), nullable=False),
    Column("message", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "collection_run",
    metadata,
    Column("run_id", String(64), primary_key=True),
    Column("command", String(128), nullable=False),
    Column("status", String(32), nullable=False),
    Column("idempotency_key", String(256), nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("finished_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("idempotency_key", name="uq_collection_run_idempotency_key"),
)

Table(
    "outbox_event",
    metadata,
    Column("event_id", String(64), primary_key=True),
    Column("contract_name", String(128), nullable=False),
    Column("contract_version", String(32), nullable=False),
    Column("aggregate_id", String(64), nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSON, nullable=False),
    Column("published_at", DateTime(timezone=True), nullable=True),
)

Table(
    "abc_quote_snapshot",
    metadata,
    Column("snapshot_id", String(64), primary_key=True),
    Column("as_of_date", Date, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "abc_quote_entry",
    metadata,
    Column("entry_id", String(64), primary_key=True),
    Column("snapshot_id", String(64), nullable=False),
    Column("instrument_code", String(32), nullable=False),
    Column("quote_status", String(32), nullable=False),
    Column("buy_price", financial_type, nullable=True),
    Column("sell_price", financial_type, nullable=True),
    Column("quote_time", DateTime(timezone=True), nullable=True),
    CheckConstraint(
        "buy_price IS NULL OR buy_price >= 0", name="ck_abc_quote_buy_price_non_negative"
    ),
    CheckConstraint(
        "sell_price IS NULL OR sell_price >= 0", name="ck_abc_quote_sell_price_non_negative"
    ),
    UniqueConstraint(
        "snapshot_id", "instrument_code", name="uq_abc_quote_snapshot_instrument"
    ),
)

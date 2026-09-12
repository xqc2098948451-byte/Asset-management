from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from alembic import command


def alembic_config(database_url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[3] / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def upgrade(database_url: str) -> None:
    command.upgrade(alembic_config(database_url), "head")


def test_upgrade_creates_only_data_collection_schema(
    database_url: str, database_engine: Engine
) -> None:
    upgrade(database_url)

    schemas = database_engine.connect().execute(
        text(
            "SELECT nspname FROM pg_namespace "
            "WHERE nspname NOT LIKE 'pg_%' AND nspname NOT IN ('information_schema', 'public') "
            "ORDER BY nspname"
        )
    ).scalars().all()
    assert schemas == ["data_collection"]


def test_schema_has_approved_internal_tables(
    database_url: str, database_engine: Engine
) -> None:
    upgrade(database_url)

    tables = database_engine.connect().execute(
        text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'data_collection' "
            "ORDER BY tablename"
        )
    ).scalars().all()
    assert tables == [
        "abc_quote_entry",
        "abc_quote_snapshot",
        "canonical_snapshot",
        "collection_run",
        "data_quality_alert",
        "data_source",
        "investment_plan_version",
        "market_calendar_day",
        "market_observation",
        "monthly_account_anchor",
        "monthly_reconciliation_cycle",
        "outbox_event",
        "planned_contribution",
        "raw_evidence",
        "reconciliation_adjustment",
        "tracked_instrument",
    ]


def test_upgrade_downgrade_upgrade_is_repeatable(database_url: str) -> None:
    config = alembic_config(database_url)

    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")


def test_financial_columns_use_numeric_28_10(
    database_url: str, database_engine: Engine
) -> None:
    upgrade(database_url)

    columns = {
        column["name"]: column["type"]
        for column in inspect(database_engine).get_columns(
            "monthly_account_anchor", schema="data_collection"
        )
    }
    for name in ("account_value", "confirmed_units", "pending_amount", "pending_units"):
        assert columns[name].precision == 28
        assert columns[name].scale == 10


def test_non_negative_financial_constraints_are_enforced(
    database_url: str, database_engine: Engine
) -> None:
    upgrade(database_url)

    with pytest.raises(IntegrityError), database_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO data_collection.monthly_account_anchor "
                "(anchor_id, instrument_code, snapshot_as_of_date, confirmed_at, "
                "confirmed_units, account_value, source, quality_status, "
                "reconciliation_status) VALUES "
                "('anchor-negative', '019172', '2026-08-31', "
                "'2026-09-05T09:00:00+00:00', -1, 1, "
                "'MANUAL_MONTHLY_CONFIRMATION', 'VALID', 'RECONCILED')"
            )
        )

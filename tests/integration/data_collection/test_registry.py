from pathlib import Path

from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import Engine

from alembic import command
from asset_management.data_collection.adapters.database.registry import seed_registries
from asset_management.data_collection.domain.enums import SourcePolicy


def alembic_config(database_url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[3] / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def upgrade(database_url: str) -> None:
    command.upgrade(alembic_config(database_url), "head")


def test_source_policy_contains_only_approved_values() -> None:
    assert set(SourcePolicy) == {
        SourcePolicy.AUTO_ALLOWED,
        SourcePolicy.MANUAL_DOWNLOAD,
        SourcePolicy.MANUAL_INPUT,
        SourcePolicy.DISABLED,
    }
    assert "OPTIONAL" not in SourcePolicy.__members__


def test_seed_creates_exact_approved_sources_and_instruments(
    database_url: str, database_engine: Engine
) -> None:
    upgrade(database_url)
    seed_registries(database_engine)

    with database_engine.connect() as connection:
        sources = connection.execute(
            text("SELECT source_code, policy FROM data_collection.data_source ORDER BY source_code")
        ).all()
    assert sources == [
        ("ABC_ACCOUNT_STATEMENT", "MANUAL_DOWNLOAD"),
        ("ABC_BOND_PRODUCT_UNIVERSE", "MANUAL_DOWNLOAD"),
        ("ABC_DAILY_QUOTES", "MANUAL_DOWNLOAD"),
        ("ABC_RISK_LEVEL", "DISABLED"),
        ("CBOND_VALUATION", "MANUAL_DOWNLOAD"),
        ("CBOND_YIELD_CURVE", "MANUAL_DOWNLOAD"),
        ("CHINAMONEY_BOND_MASTER", "MANUAL_DOWNLOAD"),
        ("CN_TRADING_CALENDAR", "MANUAL_DOWNLOAD"),
    ]

    with database_engine.connect() as connection:
        instruments = connection.execute(
            text(
                "SELECT instrument_code, verification_status, fund_name, category, benchmark "
                "FROM data_collection.tracked_instrument ORDER BY instrument_code"
            )
        ).all()
    assert [row[0] for row in instruments] == [
        "000307",
        "002963",
        "016452",
        "017641",
        "019172",
        "020602",
        "021707",
        "161125",
        "161130",
    ]
    assert all(row[1] == "UNVERIFIED" for row in instruments)
    assert all(row[2:] == (None, None, None) for row in instruments)


def test_seed_repairs_legacy_optional_risk_policy_and_is_idempotent(
    database_url: str, database_engine: Engine
) -> None:
    upgrade(database_url)
    with database_engine.begin() as connection:
        connection.execute(
            text("DELETE FROM data_collection.data_source")
        )
        connection.execute(
            text(
                "INSERT INTO data_collection.data_source "
                "(source_id, source_code, policy) "
                "VALUES ('ABC_RISK_LEVEL', 'ABC_RISK_LEVEL', 'OPTIONAL')"
            )
        )

    seed_registries(database_engine)
    seed_registries(database_engine)

    with database_engine.connect() as connection:
        policy = connection.execute(
            text(
                "SELECT policy FROM data_collection.data_source "
                "WHERE source_code = 'ABC_RISK_LEVEL'"
            )
        ).scalar_one()
    assert policy == "DISABLED"


def test_seed_does_not_overwrite_a_non_legacy_risk_policy(
    database_url: str, database_engine: Engine
) -> None:
    upgrade(database_url)
    with database_engine.begin() as connection:
        connection.execute(text("DELETE FROM data_collection.data_source"))
        connection.execute(
            text(
                "INSERT INTO data_collection.data_source "
                "(source_id, source_code, policy) "
                "VALUES ('ABC_RISK_LEVEL', 'ABC_RISK_LEVEL', 'MANUAL_INPUT')"
            )
        )

    seed_registries(database_engine)

    with database_engine.connect() as connection:
        policy = connection.execute(
            text(
                "SELECT policy FROM data_collection.data_source "
                "WHERE source_code = 'ABC_RISK_LEVEL'"
            )
        ).scalar_one()
    assert policy == "MANUAL_INPUT"


def test_seed_is_idempotent_and_never_enables_automatic_sources(
    database_url: str, database_engine: Engine
) -> None:
    upgrade(database_url)
    seed_registries(database_engine)
    seed_registries(database_engine)

    with database_engine.connect() as connection:
        counts = connection.execute(
            text(
                "SELECT (SELECT count(*) FROM data_collection.data_source), "
                "(SELECT count(*) FROM data_collection.tracked_instrument), "
                "(SELECT count(*) FROM data_collection.data_source WHERE policy = 'AUTO_ALLOWED')"
            )
        ).one()
    assert counts == (8, 9, 0)

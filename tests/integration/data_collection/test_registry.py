from pathlib import Path

from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import Engine

from alembic import command
from asset_management.data_collection.adapters.database.registry import seed_registries


def alembic_config(database_url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[3] / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def upgrade(database_url: str) -> None:
    command.upgrade(alembic_config(database_url), "head")


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
        ("ABC_RISK_LEVEL", "OPTIONAL"),
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

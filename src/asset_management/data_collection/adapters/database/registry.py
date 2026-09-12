from collections.abc import Mapping

from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert

from asset_management.data_collection.domain.enums import SourcePolicy

from .schema import SCHEMA, metadata

SOURCE_POLICIES: Mapping[str, SourcePolicy] = {
    "CBOND_VALUATION": SourcePolicy.MANUAL_DOWNLOAD,
    "CBOND_YIELD_CURVE": SourcePolicy.MANUAL_DOWNLOAD,
    "CHINAMONEY_BOND_MASTER": SourcePolicy.MANUAL_DOWNLOAD,
    "ABC_BOND_PRODUCT_UNIVERSE": SourcePolicy.MANUAL_DOWNLOAD,
    "ABC_DAILY_QUOTES": SourcePolicy.MANUAL_DOWNLOAD,
    "ABC_RISK_LEVEL": SourcePolicy.OPTIONAL,
    "ABC_ACCOUNT_STATEMENT": SourcePolicy.MANUAL_DOWNLOAD,
    "CN_TRADING_CALENDAR": SourcePolicy.MANUAL_DOWNLOAD,
}

TRACKED_INSTRUMENT_CODES = (
    "019172",
    "017641",
    "016452",
    "021707",
    "000307",
    "020602",
    "161130",
    "161125",
    "002963",
)


def seed_registries(engine: Engine) -> None:
    data_source = metadata.tables[f"{SCHEMA}.data_source"]
    tracked_instrument = metadata.tables[f"{SCHEMA}.tracked_instrument"]

    with engine.begin() as connection:
        for source_code, policy in SOURCE_POLICIES.items():
            statement = insert(data_source).values(
                source_id=source_code,
                source_code=source_code,
                policy=policy.value,
            )
            connection.execute(statement.on_conflict_do_nothing(index_elements=["source_code"]))

        for instrument_code in TRACKED_INSTRUMENT_CODES:
            statement = insert(tracked_instrument).values(
                instrument_id=instrument_code,
                instrument_code=instrument_code,
                verification_status="UNVERIFIED",
            )
            connection.execute(
                statement.on_conflict_do_nothing(index_elements=["instrument_code"])
            )

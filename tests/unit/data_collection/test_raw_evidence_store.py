from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from asset_management.data_collection.adapters.database.raw_evidence import (
    persist_raw_evidence_metadata,
)
from asset_management.data_collection.adapters.filesystem_raw_store import (
    FilesystemRawEvidenceStore,
    RawEvidenceIntegrityError,
)
from asset_management.data_collection.ports.raw_evidence_store import RawEvidenceRef


def test_put_get_round_trip_is_sha256_addressed(tmp_path: Path) -> None:
    store = FilesystemRawEvidenceStore(tmp_path)
    content = b"fund statement\nvalue=123.45\n"

    reference = store.put(content, original_filename="statement.txt")

    assert isinstance(reference, RawEvidenceRef)
    assert reference.content_sha256 == (
        "1a363efe0cb1b5391718735b49b674b01dbedee86fd6b6e5513f20b6c268b20f"
    )
    assert store.get(reference) == content


def test_same_content_reuses_identity_and_different_content_does_not(tmp_path: Path) -> None:
    store = FilesystemRawEvidenceStore(tmp_path)

    first = store.put(b"same")
    second = store.put(b"same")
    different = store.put(b"different")

    assert first == second
    assert first.content_sha256 != different.content_sha256


def test_corrupted_content_address_cannot_be_silently_overwritten(tmp_path: Path) -> None:
    store = FilesystemRawEvidenceStore(tmp_path)
    content = b"immutable"
    reference = store.put(content)
    Path(reference.storage_uri).write_bytes(b"corrupted")

    with pytest.raises(RawEvidenceIntegrityError):
        store.put(content)


def test_database_metadata_matches_persisted_evidence(
    tmp_path: Path, database_url: str, database_engine: Engine
) -> None:
    from alembic.config import Config

    from alembic import command

    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[3] / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")

    store = FilesystemRawEvidenceStore(tmp_path)
    content = b"raw-evidence"
    reference = store.put(content, original_filename="source.csv", metadata={"row": 1})
    persist_raw_evidence_metadata(
        database_engine,
        reference,
        original_filename="source.csv",
        metadata={"row": 1},
        collected_at=datetime(2026, 9, 12, tzinfo=UTC),
    )

    with database_engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT content_sha256, storage_uri, original_filename, metadata "
                "FROM data_collection.raw_evidence WHERE evidence_id = :evidence_id"
            ),
            {"evidence_id": reference.evidence_id},
        ).one()
    assert row == (
        reference.content_sha256,
        reference.storage_uri,
        "source.csv",
        {"row": 1},
    )

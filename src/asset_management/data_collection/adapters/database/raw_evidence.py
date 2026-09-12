from datetime import datetime

from sqlalchemy import Engine, select

from asset_management.data_collection.ports.raw_evidence_store import RawEvidenceRef

from .schema import SCHEMA
from .schema import metadata as db_metadata


class RawEvidenceMetadataMismatchError(RuntimeError):
    """Raised when an evidence id is associated with different metadata."""


def persist_raw_evidence_metadata(
    engine: Engine,
    reference: RawEvidenceRef,
    *,
    original_filename: str | None,
    metadata: dict[str, object],
    collected_at: datetime,
) -> None:
    raw_evidence = db_metadata.tables[f"{SCHEMA}.raw_evidence"]
    values = {
        "evidence_id": reference.evidence_id,
        "content_sha256": reference.content_sha256,
        "storage_uri": reference.storage_uri,
        "original_filename": original_filename,
        "metadata": metadata,
        "collected_at": collected_at,
    }

    with engine.begin() as connection:
        existing = connection.execute(
            select(raw_evidence).where(raw_evidence.c.evidence_id == reference.evidence_id)
        ).mappings().one_or_none()
        if existing is not None:
            if any(existing[key] != value for key, value in values.items()):
                raise RawEvidenceMetadataMismatchError(
                    f"metadata for evidence {reference.evidence_id} does not match"
                )
            return
        connection.execute(raw_evidence.insert().values(**values))

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class RawEvidenceRef:
    evidence_id: str
    content_sha256: str
    storage_uri: str

    @classmethod
    def from_path(cls, content_sha256: str, path: Path) -> "RawEvidenceRef":
        return cls(
            evidence_id=content_sha256,
            content_sha256=content_sha256,
            storage_uri=str(path),
        )


class RawEvidenceStore(Protocol):
    def put(
        self,
        content: bytes,
        *,
        original_filename: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> RawEvidenceRef:
        ...

    def get(self, reference: RawEvidenceRef) -> bytes:
        ...

import hashlib
import os
from pathlib import Path

from asset_management.data_collection.ports.raw_evidence_store import RawEvidenceRef


class RawEvidenceIntegrityError(RuntimeError):
    """Raised when content no longer matches its content-addressed identity."""


class FilesystemRawEvidenceStore:
    def __init__(self, root: Path | None = None) -> None:
        configured_root = root or self._configured_root()
        self.root = configured_root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _configured_root() -> Path:
        configured = os.environ.get("RAW_EVIDENCE_ROOT")
        if not configured:
            raise ValueError("RAW_EVIDENCE_ROOT must be configured")
        return Path(configured)

    def put(
        self,
        content: bytes,
        *,
        original_filename: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> RawEvidenceRef:
        del original_filename, metadata
        content_sha256 = hashlib.sha256(content).hexdigest()
        path = self.root / content_sha256[:2] / content_sha256
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            self._verify_existing(path, path.read_bytes(), content_sha256)
            return RawEvidenceRef.from_path(content_sha256, path)

        try:
            with path.open("xb") as evidence_file:
                evidence_file.write(content)
        except FileExistsError:
            self._verify_existing(path, content, content_sha256)
        return RawEvidenceRef.from_path(content_sha256, path)

    def get(self, reference: RawEvidenceRef) -> bytes:
        content = Path(reference.storage_uri).read_bytes()
        self._verify_existing(Path(reference.storage_uri), content, reference.content_sha256)
        return content

    @staticmethod
    def _verify_existing(path: Path, content: bytes, expected_sha256: str) -> None:
        actual_sha256 = hashlib.sha256(content).hexdigest()
        if actual_sha256 != expected_sha256:
            raise RawEvidenceIntegrityError(
                f"content at {path} has hash {actual_sha256}, expected {expected_sha256}"
            )

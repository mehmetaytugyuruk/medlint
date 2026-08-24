"""medlint: deterministic medical-imaging split-integrity audits."""

from importlib import metadata as _metadata

from .api import audit, audit_manifest, audit_split_roots
from .config import AuditConfig, DatasetSpec, SplitSpec
from .evidence import AuditResult, EvidenceCategory, Finding

try:
    __version__ = _metadata.version("medlint")
except _metadata.PackageNotFoundError:
    __version__ = "0+local"

__all__ = [
    "AuditConfig",
    "AuditResult",
    "DatasetSpec",
    "EvidenceCategory",
    "Finding",
    "SplitSpec",
    "__version__",
    "audit",
    "audit_manifest",
    "audit_split_roots",
]

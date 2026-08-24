"""Local, read-only dataset input adapters."""

from .discovery import DiscoveredArtifact, DiscoveryError, discover

__all__ = ["DiscoveredArtifact", "DiscoveryError", "discover"]

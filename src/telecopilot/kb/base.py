from abc import ABC, abstractmethod

from telecopilot.kb.models import DocumentChunk, ExtractedDocument


class BaseExtractor(ABC):
    """Abstract base class for document and web extractors (Factory target)."""

    @abstractmethod
    def extract(self, file_path_or_url: str) -> ExtractedDocument:
        """Extract text, sections, and metadata from source document or live URL."""
        pass


class BaseChunker(ABC):
    """Abstract base class for specialized policy chunkers (Factory target)."""

    @abstractmethod
    def chunk(self, document: ExtractedDocument) -> list[DocumentChunk]:
        """Split extracted document into semantic, policy-grounded chunks."""
        pass

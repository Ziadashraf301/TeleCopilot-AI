from typing import Any

from pydantic import BaseModel, Field


class SparseVectorData(BaseModel):
    """Indices and values for Qdrant sparse vector."""

    indices: list[int] = Field(default_factory=list, description="Non-zero sparse dimension indices")
    values: list[float] = Field(default_factory=list, description="BM25/Lexical term frequency weights")


class DocumentChunk(BaseModel):
    """
    Represents a chunk of a document stored in Qdrant vector collection.
    Supports both Dense vectors (Cohere) and Sparse vectors (BM25/Lexical).
    """

    chunk_id: str
    content: str
    source: str
    source_modality: str
    policy_type: str
    intent_category: str
    section_title: str
    page_number: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    dense_vector: list[float] | None = None
    sparse_vector: SparseVectorData | None = None


class SearchResult(BaseModel):
    """Represents a retrieved document chunk with similarity scores and intent information."""

    chunk_id: str
    content: str
    source: str
    source_modality: str
    policy_type: str
    intent_category: str
    section_title: str
    score: float
    page_number: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedDocument(BaseModel):
    """Normalized document representation output by extractors."""

    document_id: str
    source_path: str
    title: str
    raw_text: str
    policy_type: str
    sections: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

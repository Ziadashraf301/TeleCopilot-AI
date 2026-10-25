import pytest
from telecopilot.ingestion.chunkers.policy_chunkers import (
    SIMPolicyChunker,
    WifiPolicyChunker,
    BillingPolicyChunker,
    WebScrapedPolicyChunker,
)
from telecopilot.models.document_models import ExtractedDocument


def test_langchain_splitters_in_chunkers():
    """Verify all 4 chunkers utilize LangChain RecursiveCharacterTextSplitters."""
    # Test SIM Chunker
    sim_chunker = SIMPolicyChunker(chunk_size=200, chunk_overlap=30)
    assert hasattr(sim_chunker, "text_splitter")

    doc = ExtractedDocument(
        document_id="doc_test_1",
        source_path="test_sim.html",
        title="SIM Policy Test",
        raw_text="Long text " * 50,
        policy_type="sim_replacement",
        sections=[{
            "section_title": "eSIM Activation Steps",
            "content": "Step 1: Open app. " * 30,
            "page_number": 1
        }]
    )

    chunks = sim_chunker.chunk(doc)
    assert len(chunks) > 1
    assert chunks[0].intent_category == "SIM_MANAGEMENT"
    assert chunks[0].metadata["splitter"] == "LangChain_RecursiveCharacter"

    # Test Web Scraped Chunker
    web_chunker = WebScrapedPolicyChunker(chunk_size=300, chunk_overlap=50)
    assert hasattr(web_chunker, "text_splitter")

    web_doc = ExtractedDocument(
        document_id="doc_web_1",
        source_path="https://www.te.eg/",
        title="WE Egypt Web",
        raw_text="WE Space Mega Plan Details. " * 40,
        policy_type="telecom_egypt_web",
        sections=[{
            "section_title": "WE Space Super Mega Ultra",
            "content": "Super 30Mbps 140GB. Mega 70Mbps 250GB. Ultra 100Mbps 600GB. " * 15,
            "page_number": 1
        }]
    )

    web_chunks = web_chunker.chunk(web_doc)
    assert len(web_chunks) > 1
    assert web_chunks[0].intent_category == "PLANS_AND_OFFERS"
    assert web_chunks[0].metadata["splitter"] == "LangChain_WebSemanticSplitter"

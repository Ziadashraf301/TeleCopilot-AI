import pytest

from telecopilot.kb.chunkers.policy_chunkers import (
    BillingPolicyChunker,
    SIMPolicyChunker,
    WebScrapedPolicyChunker,
    WifiPolicyChunker,
)
from telecopilot.kb.extractors.docx_extractor import DocxExtractor
from telecopilot.kb.extractors.gemini_ocr_extractor import GeminiOCRExtractor
from telecopilot.kb.extractors.html_extractor import HTMLExtractor
from telecopilot.kb.extractors.web_scraper_extractor import WebScraperExtractor
from telecopilot.kb.factories import ChunkerFactory, ExtractorFactory


def test_extractor_factory():
    """Verify ExtractorFactory resolves correct extractors based on URL protocol or file extension."""
    web_ext = ExtractorFactory.get_extractor("https://www.te.eg/")
    assert isinstance(web_ext, WebScraperExtractor)

    html_ext = ExtractorFactory.get_extractor("sample.html")
    assert isinstance(html_ext, HTMLExtractor)

    pdf_ext = ExtractorFactory.get_extractor("policy.pdf")
    assert isinstance(pdf_ext, GeminiOCRExtractor)

    docx_ext = ExtractorFactory.get_extractor("billing.docx")
    assert isinstance(docx_ext, DocxExtractor)

    with pytest.raises(ValueError):
        ExtractorFactory.get_extractor("unknown.xyz")


def test_chunker_factory():
    """Verify ChunkerFactory produces specialized policy chunkers for all 4 types."""
    sim_chunker = ChunkerFactory.get_chunker("sim_replacement")
    assert isinstance(sim_chunker, SIMPolicyChunker)

    wifi_chunker = ChunkerFactory.get_chunker("wifi_troubleshooting")
    assert isinstance(wifi_chunker, WifiPolicyChunker)

    billing_chunker = ChunkerFactory.get_chunker("billing_refund")
    assert isinstance(billing_chunker, BillingPolicyChunker)

    web_chunker = ChunkerFactory.get_chunker("telecom_egypt_web")
    assert isinstance(web_chunker, WebScrapedPolicyChunker)

import pytest
from telecopilot.ingestion.extractors.web_scraper_extractor import WebScraperExtractor
from telecopilot.ingestion.chunkers.policy_chunkers import WebScrapedPolicyChunker


def test_web_scraper_html_parsing():
    """Verify WebScraperExtractor parses HTML structure and generates ExtractedDocument."""
    html_sample = """
    <html>
        <head><title>5G Roaming Support FAQ</title></head>
        <body>
            <header><nav>Home | Contact</nav></header>
            <h1>International 5G Roaming Guide</h1>
            <h2>Zone 1: Europe & UK</h2>
            <p>Data roaming is capped at 25GB per billing cycle without extra charge.</p>
            <h2>Zone 2: Asia Pacific</h2>
            <p>Data roaming costs $10 per day pass for unlimited high-speed access.</p>
            <footer>Copyright 2026 Telecom Inc</footer>
        </body>
    </html>
    """
    scraper = WebScraperExtractor()
    doc = scraper._parse_html_in_memory(html_sample, source_url="https://telecom.com/roaming-faq")

    assert doc.title == "5G Roaming Support FAQ"
    assert doc.policy_type == "telecom_egypt_web"
    assert len(doc.sections) >= 2
    # Ensure nav and footer were stripped
    assert "Home | Contact" not in doc.raw_text
    assert "Copyright 2026" not in doc.raw_text

    chunker = WebScrapedPolicyChunker()
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 2
    assert "https://telecom.com/roaming-faq" in chunks[0].content
    assert chunks[0].policy_type == "telecom_egypt_web"
    assert chunks[0].intent_category == "PLANS_AND_OFFERS"

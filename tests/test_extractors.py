from telecopilot.kb.chunkers.policy_chunkers import SIMPolicyChunker
from telecopilot.kb.extractors.html_extractor import HTMLExtractor


def test_html_extractor_and_sim_chunker(tmp_path):
    """Test HTML policy parsing and chunking workflow.

    HTMLExtractor derives policy_type from the file name, so the fixture is
    named like the real data/raw policy files.
    """
    html_content = """
    <html>
        <head><title>SIM Replacement Test Policy</title></head>
        <body>
            <h1>SIM Policy</h1>
            <h2>eSIM Activation</h2>
            <p>Instant eSIM activation is free of charge for all customers.</p>
            <h2>Physical SIM Store Pickup</h2>
            <p>Physical SIM pickup costs $5 unless customer is Gold Tier.</p>
        </body>
    </html>
    """
    test_file = tmp_path / "sim_replacement.html"
    test_file.write_text(html_content, encoding="utf-8")

    extractor = HTMLExtractor()
    doc = extractor.extract(str(test_file))

    assert doc.policy_type == "sim_replacement"
    assert len(doc.sections) >= 2
    assert "SIM Replacement Test Policy" in doc.title

    chunker = SIMPolicyChunker()
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 2
    assert any("eSIM" in c.content for c in chunks)
    assert chunks[0].policy_type == "sim_replacement"

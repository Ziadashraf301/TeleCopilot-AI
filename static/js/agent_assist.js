const scenarios = {
    sim: {
        text: "I lost my iPhone on the metro this morning. I need my phone number working today for work. How can I get a replacement SIM card right away?",
        intent: "SIM_MANAGEMENT"
    },
    wifi: {
        text: "My home broadband optical router has a solid RED internet light since 8 AM. I work from home and cannot connect. Can someone come fix this?",
        intent: "WIFI_TECHNICAL_SUPPORT"
    },
    billing: {
        text: "I noticed an unexpected $15.00 late payment charge on my invoice. My bank had a temporary transfer delay. Can you please waive or refund this fee?",
        intent: "BILLING_AND_PAYMENTS"
    },
    te_eg: {
        text: "عندي مشكلة في راوتر WE ولمبة النت لونها أحمر والنت فاصل، وبسأل كمان عن باقات WE Space الفايبر وسرعات الميجا والألترا واستبدال الشريحة؟",
        intent: "PLANS_AND_OFFERS"
    }
};

function toggleChatbot() {
    const widget = document.getElementById('chatWidget');
    widget.classList.toggle('active');
}

function loadScenario(type) {
    const scenario = scenarios[type];
    if (scenario) {
        document.getElementById('customerQuery').value = scenario.text;
        // Search globally across all indexed policy and scraped web modalities
        solveProblem(null);
    }
}

async function solveProblem(intentFilter = null) {
    const query = document.getElementById('customerQuery').value.trim();
    const solveBtn = document.getElementById('solveBtn');
    const solutionBody = document.getElementById('solutionBody');

    if (!query) {
        alert("Please enter a customer problem query.");
        return;
    }

    solveBtn.disabled = true;
    solveBtn.innerHTML = "<span>⏳ Retrieving & Synthesizing...</span>";

    solutionBody.innerHTML = `
        <div class="empty-state">
            <p>🔍 Searching Qdrant Hybrid Vectors & Reranking...</p>
        </div>
    `;

    try {
        const response = await fetch('/api/agent-assist/solve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_query: query,
                intent_filter: intentFilter || null
            })
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${await response.text()}`);
        }

        const data = await response.json();
        renderSolution(data);
    } catch (err) {
        console.error(err);
        solutionBody.innerHTML = `
            <div style="color: #ef4444; font-size: 0.8rem;">
                <strong>⚠️ Error:</strong> ${err.message}
            </div>
        `;
    } finally {
        solveBtn.disabled = false;
        solveBtn.innerHTML = "✨ Solve & Generate Reply";
    }
}

function renderSolution(data) {
    const solutionBody = document.getElementById('solutionBody');

    const stepsHtml = (data.actionable_agent_steps || [])
        .map(step => `<li>${step}</li>`)
        .join('');

    const citationsHtml = (data.policy_citations || [])
        .map(cit => `
            <div style="background: rgba(255,255,255,0.03); border-left: 2px solid #8b5cf6; padding: 6px 10px; margin-bottom: 6px; font-size: 0.75rem;">
                <div style="display: flex; justify-content: space-between;">
                    <strong style="color: #cbd5e1;">📜 ${cit.document}</strong>
                    <span style="color: #60a5fa; font-size: 0.68rem;">${cit.source_modality}</span>
                </div>
                <div style="color: #94a3b8; font-size: 0.72rem;">${cit.section}</div>
            </div>
        `).join('');

    solutionBody.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="badge badge-html" style="font-size: 0.68rem;">🎯 ${data.detected_intent}</span>
                <span style="font-size: 0.72rem; color: #34d399; font-weight: 700;">Status: ${data.resolution_status}</span>
            </div>

            <div style="background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.3); border-radius: 8px; padding: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 0.72rem; font-weight: 700; color: #60a5fa;">💬 Suggested CSR Reply</span>
                    <button style="background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 0.72rem;" onclick="copyReply()">📋 Copy</button>
                </div>
                <div id="replyText" style="font-size: 0.82rem; line-height: 1.5; color: #f8fafc;">${data.suggested_customer_reply}</div>
            </div>

            <div>
                <h5 style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 4px; text-transform: uppercase;">📋 Action Steps for Agent:</h5>
                <ol style="padding-left: 16px; font-size: 0.78rem; color: #cbd5e1; line-height: 1.4;">
                    ${stepsHtml}
                </ol>
            </div>

            <div>
                <h5 style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 4px; text-transform: uppercase;">🔍 Citations & Sources:</h5>
                ${citationsHtml}
            </div>

            <!-- Latency Breakdown Per Service -->
            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 8px 10px; font-size: 0.72rem;">
                <div style="font-weight: 700; color: #94a3b8; margin-bottom: 6px; display: flex; justify-content: space-between;">
                    <span>⚡ Service Latency Breakdown:</span>
                    <span style="color: #38bdf8;">Total: ${data.execution_time_seconds}s</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; color: #cbd5e1;">
                    <div>🔢 Embed (Cohere+BM25): <strong style="color: #60a5fa;">${data.latency_breakdown?.query_embedding_seconds || 0}s</strong></div>
                    <div>🔍 Qdrant Hybrid Search: <strong style="color: #a78bfa;">${data.latency_breakdown?.qdrant_hybrid_search_seconds || 0}s</strong></div>
                    <div>🎯 Cohere Rerank v3.5: <strong style="color: #f59e0b;">${data.latency_breakdown?.cohere_rerank_seconds || 0}s</strong></div>
                    <div>🤖 Gemini 3.1 LLM: <strong style="color: #34d399;">${data.latency_breakdown?.gemini_llm_synthesis_seconds || 0}s</strong></div>
                </div>
            </div>

            <div style="font-size: 0.72rem; color: #94a3b8; display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px; margin-top: 4px;">
                <span>🧩 ${data.retrieved_chunks_count} chunks retrieved</span>
                <span>🔢 ${data.total_tokens} tokens &bull; <strong style="color: #34d399;">$${data.estimated_cost_usd} USD</strong></span>
            </div>
        </div>
    `;

}

function copyReply() {
    const text = document.getElementById('replyText').innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert("Suggested response copied to clipboard!");
    });
}

async function runFullPipeline() {
    const status = document.getElementById('pipelineStatus');
    status.style.color = "#f59e0b";
    status.textContent = "⏳ Scraping website & indexing policies into Qdrant...";
    try {
        const res = await fetch('/api/ingest/all', { method: 'POST' });
        const data = await res.json();
        status.style.color = "#10b981";
        status.textContent = `✅ Successfully scraped & indexed ${data.pages_scraped} sources into Qdrant!`;
    } catch (e) {
        status.style.color = "#ef4444";
        status.textContent = `❌ Pipeline failed: ${e.message}`;
    }
}

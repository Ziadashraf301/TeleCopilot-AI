/**
 * TELECOM CONNECT - AGENT ASSIST & IN-PAGE DOCUMENT VIEWER
 * Handles AI CSR query solving, in-page document reading, and interactive filtering.
 */

// Quick test scenarios covering both Arabic & English modalities
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
    },
    roaming: {
        text: "Traveling to Saudi Arabia tomorrow. What is the daily Roaming Passport rate and how to activate it?",
        intent: "ROAMING_AND_INTERNATIONAL"
    },
    ftth: {
        text: "What is the acceptable optical power attenuation dBm range for home FTTH fiber drop cable installation before customer sign-off?",
        intent: "BROADBAND_INSTALLATION"
    },
    sla_b2b: {
        text: "ما هي نسبة التعويض المالي وغرامات انقطاع الخدمة في اتفاقية مستوى الخدمة الماسية للشركات Diamond SLA عند انقطاع كابل الفايبر المخصص؟",
        intent: "ENTERPRISE_B2B_SUPPORT"
    },
    fraud: {
        text: "Customer suspects their mobile line was targeted by a SIM swap fraud. What is the mandatory 24-hour financial SMS lock and identity verification protocol?",
        intent: "FRAUD_AND_SECURITY"
    },
    router_ar: {
        text: "راوتر VDSL موديل DN8245V لمبة LOS بتنور أحمر وتصفح الإنترنت فاصل ومؤشر SNR Margin ضعيف، كيف يتم الفحص والاستبدال؟",
        intent: "ROUTER_HARDWARE_SUPPORT"
    }
};

/* --------------------------------------------------------------------------
   IN-PAGE DOCUMENT VIEWER (OPENS FILES DIRECTLY IN THE WEBSITE)
   -------------------------------------------------------------------------- */
function openDocumentViewer(filePath, customTitle = null) {
    if (!filePath) return;

    const modalBackdrop = document.getElementById('docModalBackdrop');
    const modalTitle = document.getElementById('modalFileTitle');
    const modalMeta = document.getElementById('modalFileMeta');
    const modalIcon = document.getElementById('modalFileIcon');
    const modalRawLink = document.getElementById('modalRawLink');
    const docFrame = document.getElementById('docFrame');
    const modalLoader = document.getElementById('modalLoader');

    // Show loader
    modalLoader.classList.remove('hidden');

    // Handle external web links (e.g. te.eg) — open in new tab since most sites block iframe embedding
    if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
        window.open(filePath, '_blank', 'noopener,noreferrer');
        return;
    }

    // Clean filename (strip directories like 'data/raw/')
    const cleanFilename = filePath.replace(/^.*[\\\/]/, '').trim();

    // Determine extension and icon
    const ext = cleanFilename.split('.').pop().toLowerCase();
    let icon = '📄';
    let typeName = 'Document';

    if (ext === 'pdf') {
        icon = '📄';
        typeName = 'PDF Document';
    } else if (ext === 'docx') {
        icon = '📝';
        typeName = 'Word DOCX';
    } else if (ext === 'html') {
        icon = '🌐';
        typeName = 'HTML Policy Guide';
    } else if (ext === 'xml') {
        icon = '📊';
        typeName = 'XML Data Structure';
    }

    modalIcon.innerText = icon;
    modalTitle.innerText = customTitle || cleanFilename;
    modalMeta.innerText = `Ground Truth File: ${cleanFilename} (${typeName}) | Qdrant Indexed`;

    // Preview URL & Raw Download Link
    const previewUrl = `/api/v1/files/preview/${cleanFilename}`;
    const rawUrl = `/api/v1/files/raw/${cleanFilename}`;

    modalRawLink.href = rawUrl;
    docFrame.src = previewUrl;

    // Show modal
    modalBackdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function handleFrameLoaded() {
    const modalLoader = document.getElementById('modalLoader');
    if (modalLoader) {
        modalLoader.classList.add('hidden');
    }
}

function closeDocumentViewer(event = null) {
    const modalBackdrop = document.getElementById('docModalBackdrop');
    const docFrame = document.getElementById('docFrame');
    if (modalBackdrop) {
        modalBackdrop.classList.remove('active');
    }
    if (docFrame) {
        docFrame.src = 'about:blank';
    }
    document.body.style.overflow = 'auto';
}

function toggleModalFullscreen() {
    const modalWindow = document.getElementById('docModalWindow');
    if (modalWindow) {
        modalWindow.classList.toggle('fullscreen');
    }
}

// Close on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeDocumentViewer();
    }
});

/* --------------------------------------------------------------------------
   COPILOT DRAWER & AI PROBLEM SOLVER
   -------------------------------------------------------------------------- */
function toggleChatbot() {
    const widget = document.getElementById('chatWidget');
    widget.classList.toggle('active');
}

function loadScenario(type) {
    const scenario = scenarios[type];
    if (scenario) {
        document.getElementById('customerQuery').value = scenario.text;
        solveProblem(null);
    }
}

function selectPlan(planName) {
    toggleChatbot();
    document.getElementById('customerQuery').value = `I am interested in the ${planName}. Can you explain its features, benefits, and price lock rules?`;
    solveProblem(null);
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
            <div class="spinner" style="margin: 0 auto 12px auto; width: 32px; height: 32px;"></div>
            <p>🔍 Searching Qdrant Hybrid Vectors & Reranking Ground Truth Policies...</p>
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
            <div style="color: #ef4444; font-size: 0.85rem; padding: 12px; background: #fee2e2; border-radius: 8px;">
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

    // RENDER INTERACTIVE CLICKABLE CITATIONS THAT OPEN FILES DIRECTLY IN THE WEBSITE
    const citationsHtml = (data.policy_citations || []).map(cit => {
        const docName = cit.document || 'Policy Document';
        const sectionName = cit.section || 'General Policy';
        const modality = cit.source_modality || 'DOCUMENT';
        // Normalize backslashes to forward slashes (Windows paths) and escape quotes for onclick
        const safeDoc = docName.replace(/\\/g, '/').replace(/'/g, "\\'");
        const safeSec = sectionName.replace(/\\/g, '/').replace(/'/g, "\\'");

        return `
            <div class="citation-item" onclick="openDocumentViewer('${safeDoc}', '${safeSec}')" title="Click to view file in website reader">
                <div class="citation-header">
                    <span class="citation-link">📜 ${docName}</span>
                    <span class="citation-modality">${modality}</span>
                </div>
                <div class="citation-section">${sectionName}</div>
                <div style="font-size: 0.72rem; color: #ED0000; font-weight: 700; margin-top: 5px; display: flex; align-items: center; gap: 4px;">
                    <span>📖 Open & Read File in Website &rarr;</span>
                </div>
            </div>
        `;
    }).join('');

    // Latency metrics — use correct field names from backend response
    const lat = data.latency_breakdown || {};
    const totalSec = data.execution_time_seconds ? data.execution_time_seconds.toFixed(3) : '0.000';
    const embMs = lat.query_embedding_seconds ? (lat.query_embedding_seconds * 1000).toFixed(0) : '0';
    const qdrantMs = lat.qdrant_hybrid_search_seconds ? (lat.qdrant_hybrid_search_seconds * 1000).toFixed(0) : '0';
    const rerankMs = lat.cohere_rerank_seconds ? (lat.cohere_rerank_seconds * 1000).toFixed(0) : '0';
    const llmMs = lat.gemini_llm_synthesis_seconds ? (lat.gemini_llm_synthesis_seconds * 1000).toFixed(0) : '0';

    solutionBody.innerHTML = `
        <div class="solution-box">
            <div class="solution-meta-bar">
                <span class="intent-tag">🎯 ${data.detected_intent}</span>
                <span class="status-tag">Status: ${data.resolution_status}</span>
            </div>

            <div class="reply-card">
                <div class="reply-header">
                    <span class="reply-title">💬 SUGGESTED CSR REPLY</span>
                    <button class="copy-btn" onclick="copyReply()">📋 Copy Reply</button>
                </div>
                <div id="replyText" class="reply-content">${data.suggested_customer_reply}</div>
            </div>

            <div class="steps-box">
                <div class="steps-title">📋 Action Steps for Agent:</div>
                <ol class="steps-list">
                    ${stepsHtml}
                </ol>
            </div>

            <div class="citations-box">
                <div class="citations-title">
                    <span>🔍 Citations & Ground Truth:</span>
                    <small style="color: #6B7280; font-weight: normal; text-transform: none;">(Click any source to read)</small>
                </div>
                ${citationsHtml || '<p style="color: #6b7280; font-size: 0.78rem;">No explicit citations returned.</p>'}
            </div>

            <div class="latency-box">
                <div class="latency-header">
                    <span>⚡ Service Latency Breakdown:</span>
                    <span style="color: #34D399; font-weight: 800;">⏱️ ${totalSec}s Total</span>
                </div>
                <div class="latency-grid">
                    <div class="latency-item">
                        <span>Cohere Embed:</span>
                        <strong>${embMs}ms</strong>
                    </div>
                    <div class="latency-item">
                        <span>Qdrant Search:</span>
                        <strong>${qdrantMs}ms</strong>
                    </div>
                    <div class="latency-item">
                        <span>Cohere Rerank:</span>
                        <strong>${rerankMs}ms</strong>
                    </div>
                    <div class="latency-item">
                        <span>Gemini Flash:</span>
                        <strong>${llmMs}ms</strong>
                    </div>
                </div>
                <div style="font-size: 0.68rem; color: #9CA3AF; margin-top: 6px; text-align: right;">
                    ${data.retrieved_chunks_count || 0} chunks • ${data.total_tokens || 0} tokens
                </div>
            </div>
        </div>
    `;
}

function copyReply() {
    const text = document.getElementById('replyText').innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert("CSR reply copied to clipboard!");
    });
}

/* --------------------------------------------------------------------------
   FILTERING & NAVIGATION HELPERS
   -------------------------------------------------------------------------- */
function filterPolicyFormat(format, btn) {
    document.querySelectorAll('.format-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    const cards = document.querySelectorAll('.policy-card');
    cards.forEach(card => {
        const cardFormat = card.getAttribute('data-format');
        if (format === 'ALL' || cardFormat === format) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

function filterDeals(cat, btn) {
    document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    const cards = document.querySelectorAll('.deal-card');
    cards.forEach(card => {
        const cardCat = card.getAttribute('data-cat');
        if (cat === 'all' || cardCat === cat) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

function handleGlobalSearch(query) {
    const q = query.toLowerCase().trim();
    const cards = document.querySelectorAll('.policy-card');
    cards.forEach(card => {
        const text = card.innerText.toLowerCase();
        if (!q || text.includes(q)) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

function scrollToSection(id) {
    const el = document.getElementById(id);
    if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
    }
}

async function runFullPipeline() {
    if (!confirm("Start full pipeline synchronization from te.eg and all 10 raw policy files into Qdrant?")) {
        return;
    }
    const btn = event.target;
    btn.disabled = true;
    btn.innerText = "⏳ Ingesting & Syncing...";

    try {
        const res = await fetch('/api/ingest/rebuild', { method: 'POST' });
        const data = await res.json();
        alert(`Ingestion Pipeline Complete! Indexed ${data.ingested_sources_count || 10} sources into Qdrant.`);
    } catch (e) {
        alert("Ingestion sync error: " + e.message);
    } finally {
        btn.disabled = false;
        btn.innerText = "🔄 Sync & Re-index Qdrant";
    }
}

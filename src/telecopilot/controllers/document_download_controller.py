import os
import io
import mimetypes
import xml.dom.minidom
from typing import List, Dict, Any
import fitz  # PyMuPDF
from docx import Document
from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from core.logger import get_logger

logger = get_logger()
router = APIRouter(tags=["Document Files & Policies"])

DATA_RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
if not os.path.exists(DATA_RAW_DIR):
    DATA_RAW_DIR = os.path.abspath(os.path.join(os.getcwd(), "data", "raw"))

POLICY_CATALOG = [
    {
        "id": "sim_replacement",
        "filename": "sim_replacement_policy.html",
        "title": "SIM Card Replacement & Digital eSIM Activation Guidelines",
        "format": "HTML",
        "language": "EN",
        "category": "Mobile & SIM",
        "description": "Lost SIM reporting, biometric ID verification, instant QR-code eSIM provisioning, and line security bars.",
        "icon": "📱"
    },
    {
        "id": "5g_troubleshooting",
        "filename": "5g_network_device_troubleshooting.html",
        "title": "5G Network Diagnostic & Mobile Device Troubleshooting Manual",
        "format": "HTML",
        "language": "EN",
        "category": "Technical Support",
        "description": "5G NSA/SA band lock, VoNR call dropping, APN provisioning, and modem diagnostic procedures.",
        "icon": "⚡"
    },
    {
        "id": "billing_refund",
        "filename": "billing_refund_policy.docx",
        "title": "Customer Billing Dispute, Fee Waivers & Refund Policy",
        "format": "DOCX",
        "language": "EN",
        "category": "Billing & Payments",
        "description": "Courtesy late fee waivers, roaming overage adjustments, payment plans, and dispute escalation protocols.",
        "icon": "💳"
    },
    {
        "id": "ftth_installation",
        "filename": "fiber_optic_ftth_installation_guide.docx",
        "title": "FTTH Fiber Optic Installation & Optical Line Verification Guide",
        "format": "DOCX",
        "language": "EN",
        "category": "Broadband & Fiber",
        "description": "Drop cable termination, optical power attenuation dBm acceptance, ONT fusion splicing, and site certification.",
        "icon": "🛠️"
    },
    {
        "id": "arabic_family_bundles",
        "filename": "arabic_family_bundles_migration.pdf",
        "title": "دليل تحويل باقات العائلة وباقات الاشتراك المنزلي المشترك",
        "format": "PDF",
        "language": "AR",
        "category": "Plans & Bundles",
        "description": "شروط ضم خطوط العائلة، توزيع الجيجابايتس والدقائق، وسياسات الترحيل وتوحيد الفواتير للعملاء.",
        "icon": "👨‍👩‍👧‍👦"
    },
    {
        "id": "arabic_router_diagnostics",
        "filename": "arabic_router_diagnostics_scan.pdf",
        "title": "دليل الفحص الميداني وأعطال أجهزة التوجيه والراوتر المنزلي",
        "format": "PDF",
        "language": "AR",
        "category": "Hardware & WiFi",
        "description": "تشخيص لمبات الراوتر، دلالة إشارة LOS الحمراء، استقرار خطوط VDSL/FTTH، وإجراءات استبدال الأجهزة في الفروع.",
        "icon": "📡"
    },
    {
        "id": "cybersecurity_fraud",
        "filename": "cybersecurity_account_fraud_prevention.pdf",
        "title": "Account Security, SIM Swap Prevention & Anti-Fraud Directives",
        "format": "PDF",
        "language": "EN",
        "category": "Security & Fraud",
        "description": "Mandatory 24-hour financial SMS lock, OTP credential sniffing countermeasures, and unauthorized transfer handling.",
        "icon": "🛡️"
    },
    {
        "id": "operations_manual",
        "filename": "pdf.pdf",
        "title": "Enterprise Telecom Customer Operations & Engineering Protocols",
        "format": "PDF",
        "language": "EN",
        "category": "Engineering & Ops",
        "description": "Core optical distribution frame standards, SLA dispatch parameters, and high-priority escalation trees.",
        "icon": "📜"
    },
    {
        "id": "roaming_passport",
        "filename": "roaming_passport_travel_rates.xml",
        "title": "Global Roaming Passport, Travel Zones & Data Bundles Catalog",
        "format": "XML",
        "language": "EN",
        "category": "Roaming & Travel",
        "description": "Structured XML rate cards, Tier 1/2 travel zones, fair use data thresholds, and partner carrier roaming agreements.",
        "icon": "🌍"
    },
    {
        "id": "arabic_enterprise_sla",
        "filename": "arabic_enterprise_sla_contracts.xml",
        "title": "اتفاقيات مستوى الخدمة وعقود المؤسسات والشركات B2B",
        "format": "XML",
        "language": "AR",
        "category": "B2B Enterprise",
        "description": "معايير الضمان الماسي والذهبي، جداول التعويضات المالية عن انقطاع خطوط الربط المخصصة، والتصعيد الهندسي.",
        "icon": "🏢"
    }
]


@router.get("/api/v1/policies")
async def list_policies():
    """Return catalog of all 10 raw policy documents with file sizes, formats, and URLs."""
    policies = []
    for item in POLICY_CATALOG:
        filepath = os.path.join(DATA_RAW_DIR, item["filename"])
        size_bytes = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        size_mb = round(size_bytes / (1024 * 1024), 2)
        policies.append({
            **item,
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "raw_url": f"/api/v1/files/raw/{item['filename']}",
            "preview_url": f"/api/v1/files/preview/{item['filename']}"
        })
    return {"status": "success", "count": len(policies), "policies": policies}


@router.get("/api/v1/files/raw/{filename}")
async def get_raw_file(filename: str):
    """Serve any raw file from data/raw directly with inline Content-Disposition."""
    clean_filename = os.path.basename(filename)
    filepath = os.path.join(DATA_RAW_DIR, clean_filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"File '{clean_filename}' not found in policy repository.")

    mime_type, _ = mimetypes.guess_type(filepath)
    if not mime_type:
        if clean_filename.endswith(".docx"):
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif clean_filename.endswith(".xml"):
            mime_type = "application/xml"
        else:
            mime_type = "application/octet-stream"

    return FileResponse(
        path=filepath,
        media_type=mime_type,
        headers={"Content-Disposition": f"inline; filename=\"{clean_filename}\""}
    )


@router.get("/api/v1/files/preview/{filename}")
async def get_file_preview(filename: str):
    """
    Render document preview as rich HTML for seamless in-page display.
    Supports DOCX (converted to styled HTML), XML (syntax highlighted),
    PDF (embedded viewer wrapper), and HTML (styled iframe content).
    """
    clean_filename = os.path.basename(filename)
    filepath = os.path.join(DATA_RAW_DIR, clean_filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"File '{clean_filename}' not found.")

    ext = os.path.splitext(clean_filename)[1].lower()

    meta = next((item for item in POLICY_CATALOG if item["filename"] == clean_filename), None)
    title = meta["title"] if meta else clean_filename
    is_arabic = meta.get("language") == "AR" if meta else ("arabic" in clean_filename.lower())
    direction = "rtl" if is_arabic else "ltr"
    align = "right" if is_arabic else "left"

    if ext == ".docx":
        try:
            doc = Document(filepath)
            html_parts = []
            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue
                style_name = p.style.name if p.style else ""
                if "Title" in style_name or "Heading 1" in style_name:
                    html_parts.append(f"<h2 class='doc-h2'>{text}</h2>")
                elif "Heading 2" in style_name or "Heading 3" in style_name:
                    html_parts.append(f"<h3 class='doc-h3'>{text}</h3>")
                else:
                    html_parts.append(f"<p class='doc-p'>{text}</p>")

            body_content = "\n".join(html_parts)
            preview_html = f"""<!DOCTYPE html>
<html lang="{'ar' if is_arabic else 'en'}" dir="{direction}">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #ffffff;
            color: #1a1a1a;
            padding: 30px 40px;
            margin: 0;
            line-height: 1.7;
            text-align: {align};
        }}
        .doc-header {{
            border-bottom: 3px solid #ED0000;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .doc-tag {{
            display: inline-block;
            background: #fee2e2;
            color: #ED0000;
            font-weight: 700;
            font-size: 0.75rem;
            padding: 4px 10px;
            border-radius: 4px;
            margin-bottom: 8px;
        }}
        .doc-title {{
            color: #111111;
            font-size: 1.6rem;
            margin: 0 0 8px 0;
            font-weight: 800;
        }}
        .doc-h2 {{
            color: #111111;
            font-size: 1.25rem;
            margin-top: 28px;
            margin-bottom: 12px;
            padding-bottom: 6px;
            border-bottom: 1px solid #e5e7eb;
            font-weight: 700;
        }}
        .doc-h3 {{
            color: #374151;
            font-size: 1.05rem;
            margin-top: 20px;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        .doc-p {{
            color: #4b5563;
            font-size: 0.95rem;
            margin-bottom: 12px;
        }}
    </style>
</head>
<body>
    <div class="doc-header">
        <span class="doc-tag">📄 WORD DOCUMENT (DOCX)</span>
        <h1 class="doc-title">{title}</h1>
        <div style="font-size: 0.85rem; color: #6b7280;">File: {clean_filename} | Official Internal Telecom Operations Standard</div>
    </div>
    <div class="doc-body">
        {body_content}
    </div>
</body>
</html>"""
            return HTMLResponse(content=preview_html)
        except Exception as e:
            logger.error(f"Error previewing docx: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to preview DOCX: {e}")

    elif ext == ".xml":
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                raw_xml = f.read()

            try:
                dom = xml.dom.minidom.parseString(raw_xml)
                pretty_xml = dom.toprettyxml(indent="  ")
            except Exception:
                pretty_xml = raw_xml

            escaped_xml = pretty_xml.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            preview_html = f"""<!DOCTYPE html>
<html lang="{'ar' if is_arabic else 'en'}" dir="{direction}">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: monospace, sans-serif;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 24px;
            margin: 0;
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        .xml-bar {{
            background: #252526;
            border-bottom: 2px solid #ED0000;
            padding: 12px 18px;
            margin: -24px -24px 20px -24px;
            font-family: sans-serif;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        pre {{
            margin: 0;
            white-space: pre-wrap;
            word-break: break-all;
            color: #9cdcfe;
        }}
    </style>
</head>
<body>
    <div class="xml-bar">
        <div>
            <strong style="color: #ffffff;">{title}</strong>
            <span style="font-size: 0.8rem; color: #888888; margin-left: 10px;">({clean_filename})</span>
        </div>
        <span style="background: #ED0000; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700;">XML STRUCTURED DATA</span>
    </div>
    <pre>{escaped_xml}</pre>
</body>
</html>"""
            return HTMLResponse(content=preview_html)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to preview XML: {e}")

    elif ext == ".html":
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)

    elif ext == ".pdf":
        raw_url = f"/api/v1/files/raw/{clean_filename}"
        preview_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
            background: #525659;
        }}
        embed, iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
    </style>
</head>
<body>
    <embed src="{raw_url}#toolbar=1&navpanes=1" type="application/pdf" width="100%" height="100%">
</body>
</html>"""
        return HTMLResponse(content=preview_html)

    else:
        return FileResponse(filepath)


# Legacy download routes
@router.get("/download/sim-policy")
async def get_sim_policy_html():
    filepath = os.path.join(DATA_RAW_DIR, "sim_replacement_policy.html")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>SIM Policy</h1>")


@router.get("/download/wifi-policy")
async def download_wifi_policy_pdf():
    filepath = os.path.join(DATA_RAW_DIR, "arabic_router_diagnostics_scan.pdf")
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="application/pdf", filename="wifi_troubleshooting_policy.pdf")
    return Response(content="File not found", status_code=404)


@router.get("/download/billing-policy")
async def download_billing_policy_docx():
    filepath = os.path.join(DATA_RAW_DIR, "billing_refund_policy.docx")
    if os.path.exists(filepath):
        return FileResponse(
            filepath,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="billing_refund_policy.docx"
        )
    return Response(content="File not found", status_code=404)

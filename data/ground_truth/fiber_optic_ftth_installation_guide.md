---
document_id: gt_fiber_optic_ftth_installation_guide
source_file: fiber_optic_ftth_installation_guide.docx
file_format: docx
policy_type: fiber_optic_ftth_installation_guide
title: "Section 1: Scope of Home Fiber Installations (نطاق أعمال التركيبات)"
page_count: 1
total_sections: 21
total_words: 3251
total_table_cells: 336
total_media_count: 15
critical_entities: ["100Mbps", "200Mbps"]
hierarchy:
  - id: sec_0
    title: "Fiber Optic Ftth Installation Guide"
    order: 0
    page: 1
  - id: sec_1
    title: "Section 1: Scope of Home Fiber Installations (نطاق أعمال التركيبات)"
    order: 1
    page: 1
  - id: sec_2
    title: "Section 2: Optical Power Budget & Attenuation Thresholds (مستويات الإشارة الضوئية dBm)"
    order: 2
    page: 1
  - id: sec_3
    title: "Section 3: FAT Box Splicing & Drop Cable Standards (مواصفات التوصيل وكابل السحب)"
    order: 3
    page: 1
  - id: sec_4
    title: "Section 4: Indoor ONT Setup & Wi-Fi Coverage Optimization (ضبط جهاز الراوتر والواي فاي)"
    order: 4
    page: 1
  - id: sec_5
    title: "Section 5: Fiber Field Diagnostics & Splice Quality Matrix (Part 1)"
    order: 5
    page: 1
  - id: sec_6
    title: "Section 6: Fiber Field Diagnostics & Splice Quality Matrix (Part 2)"
    order: 6
    page: 1
  - id: sec_7
    title: "Section 7: Fiber Field Diagnostics & Splice Quality Matrix (Part 3)"
    order: 7
    page: 1
  - id: sec_8
    title: "Section 8: Fiber Field Diagnostics & Splice Quality Matrix (Part 4)"
    order: 8
    page: 1
  - id: sec_9
    title: "Section 9: Fiber Field Diagnostics & Splice Quality Matrix (Part 5)"
    order: 9
    page: 1
  - id: sec_10
    title: "Section 10: Fiber Field Diagnostics & Splice Quality Matrix (Part 6)"
    order: 10
    page: 1
  - id: sec_11
    title: "Section 11: Fiber Field Diagnostics & Splice Quality Matrix (Part 7)"
    order: 11
    page: 1
  - id: sec_12
    title: "Section 12: Fiber Field Diagnostics & Splice Quality Matrix (Part 8)"
    order: 12
    page: 1
  - id: sec_13
    title: "Section 13: Fiber Field Diagnostics & Splice Quality Matrix (Part 9)"
    order: 13
    page: 1
  - id: sec_14
    title: "Section 14: Fiber Field Diagnostics & Splice Quality Matrix (Part 10)"
    order: 14
    page: 1
  - id: sec_15
    title: "Section 15: Fiber Field Diagnostics & Splice Quality Matrix (Part 11)"
    order: 15
    page: 1
  - id: sec_16
    title: "Section 16: Fiber Field Diagnostics & Splice Quality Matrix (Part 12)"
    order: 16
    page: 1
  - id: sec_17
    title: "Section 17: Fiber Field Diagnostics & Splice Quality Matrix (Part 13)"
    order: 17
    page: 1
  - id: sec_18
    title: "Section 18: Fiber Field Diagnostics & Splice Quality Matrix (Part 14)"
    order: 18
    page: 1
  - id: sec_19
    title: "Section 19: Fiber Field Diagnostics & Splice Quality Matrix (Part 15)"
    order: 19
    page: 1
  - id: sec_20
    title: "Embedded Diagrams & Visual Content"
    order: 20
    page: 1
---

<!-- section: sec_0 | title: Fiber Optic Ftth Installation Guide | page: 1 | order: 0 | parent: root -->
## Fiber Optic Ftth Installation Guide

Telecom Egypt (WE) - FTTH Fiber Optic Installation & Attenuation Standards
دليل التركيبات الفنية للألياف الضوئية FTTH وقياسات الإشارة الضوئية

<!-- section: sec_1 | title: Section 1: Scope of Home Fiber Installations (نطاق أعمال التركيبات) | page: 1 | order: 1 | parent: root -->
## Section 1: Scope of Home Fiber Installations (نطاق أعمال التركيبات)

This operational and technical manual specifies mandatory standards for all Fiber-to-the-Home (FTTH) installations, drop-cable routing, optical power testing, and indoor Optical Network Terminal (ONT) setup across Egypt. Ensures zero signal degradation and stable gigabit-speed connectivity for residential and commercial customers.
يحدد هذا الدليل المعايير القياسية الإلزامية لفرق التركيبات الميدانية والفنيين لضمان جودة توصيل كابلات الألياف الضوئية من كبائن التوزيع FAT وحتى جهاز الراوتر المنزلي.

<!-- section: sec_2 | title: Section 2: Optical Power Budget & Attenuation Thresholds (مستويات الإشارة الضوئية dBm) | page: 1 | order: 2 | parent: root -->
## Section 2: Optical Power Budget & Attenuation Thresholds (مستويات الإشارة الضوئية dBm)

Technicians must measure optical power levels using an Optical Power Meter (OPM) calibrated at 1490nm (downstream) and 1310nm (upstream) prior to customer sign-off:
- Optimal Signal Range: -15.0 dBm to -24.0 dBm (Green Status - Perfect Transmission).
- Acceptable Signal Range: -24.1 dBm to -27.0 dBm (Yellow Status - Marginal, requires cable inspection).
- Defective / Critical Signal: Worse than -27.1 dBm or below -30 dBm (Red Status - Service will experience frequent dropouts; FAT box re-splicing required immediately).
- Over-saturation Warning: Stronger than -8.0 dBm may damage ONT optical receiver diode.

<!-- section: sec_3 | title: Section 3: FAT Box Splicing & Drop Cable Standards (مواصفات التوصيل وكابل السحب) | page: 1 | order: 3 | parent: root -->
## Section 3: FAT Box Splicing & Drop Cable Standards (مواصفات التوصيل وكابل السحب)

1. Fiber Distribution Box (FAT): Ensure waterproof IP67 sealing of FAT closure.
2. Drop Cable: Use G.657.A2 bend-insensitive optical drop cable for residential routing.
3. Minimum Bending Radius: Never bend optical drop cable at a radius smaller than 15mm to avoid macro-bending light loss.
4. Optical Wall Outlet (ATB): Mount the Access Terminal Box inside the customer premises at least 30cm above floor level away from direct heat sources.

<!-- section: sec_4 | title: Section 4: Indoor ONT Setup & Wi-Fi Coverage Optimization (ضبط جهاز الراوتر والواي فاي) | page: 1 | order: 4 | parent: root -->
## Section 4: Indoor ONT Setup & Wi-Fi Coverage Optimization (ضبط جهاز الراوتر والواي فاي)

1. Connect SC/APC green-colored optical patch cord securely into the ONT PON port until a distinct mechanical click is heard.
2. Configure Wi-Fi Dual-Band operation (2.4GHz for range, 5GHz for maximum bandwidth).
3. Default SSID: Set to 'WE_Fiber_XXXXXX' with WPA3/WPA2-PSK mixed security.
4. Perform automated speed test to confirm contract speed (e.g. Ultra 100Mbps or Max 200Mbps) with ping latency under 10ms to local WE gateway.

<!-- section: sec_5 | title: Section 5: Fiber Field Diagnostics & Splice Quality Matrix (Part 1) | page: 1 | order: 5 | parent: root -->
## Section 5: Fiber Field Diagnostics & Splice Quality Matrix (Part 1)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 1.

<!-- section: sec_6 | title: Section 6: Fiber Field Diagnostics & Splice Quality Matrix (Part 2) | page: 1 | order: 6 | parent: root -->
## Section 6: Fiber Field Diagnostics & Splice Quality Matrix (Part 2)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 2.

<!-- section: sec_7 | title: Section 7: Fiber Field Diagnostics & Splice Quality Matrix (Part 3) | page: 1 | order: 7 | parent: root -->
## Section 7: Fiber Field Diagnostics & Splice Quality Matrix (Part 3)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 3.

<!-- section: sec_8 | title: Section 8: Fiber Field Diagnostics & Splice Quality Matrix (Part 4) | page: 1 | order: 8 | parent: root -->
## Section 8: Fiber Field Diagnostics & Splice Quality Matrix (Part 4)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 4.

<!-- section: sec_9 | title: Section 9: Fiber Field Diagnostics & Splice Quality Matrix (Part 5) | page: 1 | order: 9 | parent: root -->
## Section 9: Fiber Field Diagnostics & Splice Quality Matrix (Part 5)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 5.

<!-- section: sec_10 | title: Section 10: Fiber Field Diagnostics & Splice Quality Matrix (Part 6) | page: 1 | order: 10 | parent: root -->
## Section 10: Fiber Field Diagnostics & Splice Quality Matrix (Part 6)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 6.

<!-- section: sec_11 | title: Section 11: Fiber Field Diagnostics & Splice Quality Matrix (Part 7) | page: 1 | order: 11 | parent: root -->
## Section 11: Fiber Field Diagnostics & Splice Quality Matrix (Part 7)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 7.

<!-- section: sec_12 | title: Section 12: Fiber Field Diagnostics & Splice Quality Matrix (Part 8) | page: 1 | order: 12 | parent: root -->
## Section 12: Fiber Field Diagnostics & Splice Quality Matrix (Part 8)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 8.

<!-- section: sec_13 | title: Section 13: Fiber Field Diagnostics & Splice Quality Matrix (Part 9) | page: 1 | order: 13 | parent: root -->
## Section 13: Fiber Field Diagnostics & Splice Quality Matrix (Part 9)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 9.

<!-- section: sec_14 | title: Section 14: Fiber Field Diagnostics & Splice Quality Matrix (Part 10) | page: 1 | order: 14 | parent: root -->
## Section 14: Fiber Field Diagnostics & Splice Quality Matrix (Part 10)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 10.

<!-- section: sec_15 | title: Section 15: Fiber Field Diagnostics & Splice Quality Matrix (Part 11) | page: 1 | order: 15 | parent: root -->
## Section 15: Fiber Field Diagnostics & Splice Quality Matrix (Part 11)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 11.

<!-- section: sec_16 | title: Section 16: Fiber Field Diagnostics & Splice Quality Matrix (Part 12) | page: 1 | order: 16 | parent: root -->
## Section 16: Fiber Field Diagnostics & Splice Quality Matrix (Part 12)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 12.

<!-- section: sec_17 | title: Section 17: Fiber Field Diagnostics & Splice Quality Matrix (Part 13) | page: 1 | order: 17 | parent: root -->
## Section 17: Fiber Field Diagnostics & Splice Quality Matrix (Part 13)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 13.

<!-- section: sec_18 | title: Section 18: Fiber Field Diagnostics & Splice Quality Matrix (Part 14) | page: 1 | order: 18 | parent: root -->
## Section 18: Fiber Field Diagnostics & Splice Quality Matrix (Part 14)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 14.

<!-- section: sec_19 | title: Section 19: Fiber Field Diagnostics & Splice Quality Matrix (Part 15) | page: 1 | order: 19 | parent: root -->
## Section 19: Fiber Field Diagnostics & Splice Quality Matrix (Part 15)

Technical standard reference for optical OTDR trace analysis, connector cleaning with isopropyl alcohol wipes, and attenuation troubleshooting for GPON / XGS-PON splitters. Case 15.

<!-- section: sec_20 | title: Embedded Diagrams & Visual Content | page: 1 | order: 20 | parent: root -->
## Embedded Diagrams & Visual Content

# FTTH FIBER INSTALLATION WORKFLOW #1

**Optical Engineering Field Manual**

---

### Workflow Phases

| Phase | Description |
| :--- | :--- |
| **Phase 1: FAT Box Inspection** | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2: Drop Cable Pull** | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3: Optical Splicing** | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4: Power Verification** | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5: ONT Provisioning** | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6: Customer Acceptance** | Complete speed test, print sign-off report, and educate client on router LEDs. |

---

**TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD**

TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY

### FTTH Fiber Installation Workflow Document

**Header Information:**
* **Document Title:** FTTH FIBER INSTALLATION WORKFLOW #2
* **Section:** Optical Engineering Field Manual

---

### Workflow Phases

| Phase | Title | Instructions |
| :--- | :--- | :--- |
| **Phase 1** | FAT Box Inspection | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2** | Drop Cable Pull | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3** | Optical Splicing | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4** | Power Verification | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5** | ONT Provisioning | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6** | Customer Acceptance | Complete speed test, print sign-off report, and educate client on router LEDs. |

---

### Footer Information
* **Left Text:** TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD
* **Bottom Text:** TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY

This document outlines the FTTH fiber installation workflow.

### Header Information
*   **Document Title:** FTTH FIBER INSTALLATION WORKFLOW #3
*   **Manual Type:** Optical Engineering Field Manual

---

### Workflow Phases

| Phase | Title | Description |
| :--- | :--- | :--- |
| **Phase 1** | FAT Box Inspection | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2** | Drop Cable Pull | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3** | Optical Splicing | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4** | Power Verification | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5** | ONT Provisioning | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6** | Customer Acceptance | Complete speed test, print sign-off report and educate client on router LEDs. |

---

### Footer Information
*   **Record Label:** TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD
*   **Confidentiality Notice:** TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY

This is the structured transcription of the provided technical document.

***

# FTTH FIBER INSTALLATION WORKFLOW #4
**Optical Engineering Field Manual**

### Workflow Phases

| Phase | Description |
| :--- | :--- |
| **Phase 1: FAT Box Inspection** | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2: Drop Cable Pull** | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3: Optical Splicing** | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4: Power Verification** | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5: ONT Provisioning** | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6: Customer Acceptance** | Complete speed test, print sign-off report, and educate client on router LEDs. |

***

**TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD**

*TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY*

This transcription details the structured workflow for FTTH fiber installation as presented in the provided document.

### Document Headers
* **FTTH FIBER INSTALLATION WORKFLOW #5**
* **Optical Engineering Field Manual**

---

### Installation Workflow Phases

| Phase | Title | Instructions |
| :--- | :--- | :--- |
| **Phase 1** | FAT Box Inspection | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2** | Drop Cable Pull | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3** | Optical Splicing | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4** | Power Verification | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5** | ONT Provisioning | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6** | Customer Acceptance | Complete speed test, print sign-off report, and educate client on router LEDs. |

---

### Footer Information
* **TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD**
* **TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY**

This transcription covers all visible text within the provided FTTH Fiber Installation document.

***

**Header Information**
*   **FTTH FIBER INSTALLATION WORKFLOW #6**
*   **Optical Engineering Field Manual**

---

### Workflow Phases

| Phase | Title | Description |
| :--- | :--- | :--- |
| **Phase 1** | FAT Box Inspection | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2** | Drop Cable Pull | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3** | Optical Splicing | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4** | Power Verification | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5** | ONT Provisioning | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6** | Customer Acceptance | Complete speed test, print sign-off report and educate client on router LEDs. |

---

**Footer Information**
*   **TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD**
*   **TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY**

This document outlines the FTTH fiber installation workflow.

### Header Information
*   **Workflow Title:** FTTH FIBER INSTALLATION WORKFLOW #7
*   **Documentation Category:** Optical Engineering Field Manual

---

### Workflow Phases

| Phase | Title | Description |
| :--- | :--- | :--- |
| **Phase 1** | FAT Box Inspection | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2** | Drop Cable Pull | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3** | Optical Splicing | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4** | Power Verification | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5** | ONT Provisioning | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6** | Customer Acceptance | Complete speed test, print sign-off report, and educate client on router LEDs. |

---

### Footer Information
*   **Document Header/Label:** TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD
*   **Classification:** TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY

This transcription covers all visible text within the provided technical document image.

***

### Header Information
*   **FTTH FIBER INSTALLATION WORKFLOW #8**
*   **Optical Engineering Field Manual**

---

### Workflow Process Steps

| Phase | Description |
| :--- | :--- |
| **Phase 1: FAT Box Inspection** | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2: Drop Cable Pull** | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3: Optical Splicing** | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4: Power Verification** | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5: ONT Provisioning** | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6: Customer Acceptance** | Complete speed test, print sign-off report and educate client on router LEDs. |

---

### Footer and Metadata
*   **TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD**
*   **TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY**

This document provides the structured transcription of the FTTH installation workflow.

### Header Information
*   **Document Title:** FTTH FIBER INSTALLATION WORKFLOW #9
*   **Manual Type:** Optical Engineering Field Manual

---

### Installation Workflow Phases

| Phase | Title | Instructions |
| :--- | :--- | :--- |
| **Phase 1** | FAT Box Inspection | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2** | Drop Cable Pull | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3** | Optical Splicing | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4** | Power Verification | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5** | ONT Provisioning | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6** | Customer Acceptance | Complete speed test, print sign-off report, and educate client on router LEDs. |

---

### Footer & Metadata
*   **Field Report Section:** TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD
*   **Classification:** TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY

### Document Metadata
* **Document Title:** FTTH FIBER INSTALLATION WORKFLOW #10
* **Department/Category:** Optical Engineering Field Manual
* **Security/Footer Notice:** TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY

---

### Installation Workflow Phases

| Phase | Title | Description/Action Items |
| :--- | :--- | :--- |
| **Phase 1** | FAT Box Inspection | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2** | Drop Cable Pull | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3** | Optical Splicing | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4** | Power Verification | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5** | ONT Provisioning | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6** | Customer Acceptance | Complete speed test, print sign-off report and educate client on router LEDs. |

---

### Additional Fields
* **Footer Table Label:** TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD

This document outlines the FTTH fiber installation workflow.

### Header Information
*   **Document Title:** FTTH FIBER INSTALLATION WORKFLOW #11
*   **Department/Category:** Optical Engineering Field Manual

---

### Installation Workflow Steps

| Phase | Title | Instructions |
| :--- | :--- | :--- |
| **Phase 1** | FAT Box Inspection | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2** | Drop Cable Pull | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3** | Optical Splicing | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4** | Power Verification | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5** | ONT Provisioning | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6** | Customer Acceptance | Complete speed test, print sign-off report and educate client on router LEDs. |

---

### Footer Information
*   **Form Header:** TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD
*   **Confidentiality Notice:** TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY

Based on the provided image, here is the structured transcription of the document:

### Header Information
*   **Document Title:** FTTH FIBER INSTALLATION WORKFLOW #12
*   **Document Type:** Optical Engineering Field Manual

---

### Workflow Process (6-Phase Flowchart)

| Phase | Title | Description |
| :--- | :--- | :--- |
| **Phase 1** | FAT Box Inspection | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **Phase 2** | Drop Cable Pull | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **Phase 3** | Optical Splicing | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **Phase 4** | Power Verification | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **Phase 5** | ONT Provisioning | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **Phase 6** | Customer Acceptance | Complete speed test, print sign-off report and educate client on router LEDs. |

---

### Footer Information
*   **Record Identification:** TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD
*   **Confidentiality Notice:** TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY

This document outlines the FTTH installation workflow. Below is the structured transcription of the provided image.

### Document Header
*   **Title:** FTTH FIBER INSTALLATION WORKFLOW #13
*   **Subtitle:** Optical Engineering Field Manual

---

### Installation Workflow Steps

| Phase | Title | Description |
| :--- | :--- | :--- |
| 1 | FAT Box Inspection | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| 2 | Drop Cable Pull | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| 3 | Optical Splicing | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| 4 | Power Verification | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| 5 | ONT Provisioning | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| 6 | Customer Acceptance | Complete speed test, print sign-off report and educate client on router LEDs. |

---

### Footer Information
*   **Log/Reference:** TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD
*   **Legal Notice:** TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY

This transcription captures all text and structure from the provided FTTH Fiber Installation Workflow diagram.

---

### Header Information
*   **Workflow Title:** FTTH FIBER INSTALLATION WORKFLOW #14
*   **Document Type:** Optical Engineering Field Manual

---

### Installation Workflow Stages

| Phase | Title | Description |
| :--- | :--- | :--- |
| **1** | **FAT Box Inspection** | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **2** | **Drop Cable Pull** | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **3** | **Optical Splicing** | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **4** | **Power Verification** | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **5** | **ONT Provisioning** | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **6** | **Customer Acceptance** | Complete speed test, print sign-off report, and educate client on router LEDs. |

---

### Footer and Metadata
*   **Table Label:** TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD
*   **Confidentiality Notice:** TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY

This transcription captures all text and structural elements from the provided technical document.

---

### **Header Information**
*   **Document Title:** FTTH FIBER INSTALLATION WORKFLOW #15
*   **Manual Type:** Optical Engineering Field Manual

---

### **Workflow Phases**

| Phase | Title | Description |
| :--- | :--- | :--- |
| **1** | FAT Box Inspection | Inspect street FAT box, measure optical input dBm with calibrated OPM. |
| **2** | Drop Cable Pull | Route G.657.A2 drop cable via internal building conduit respecting 15mm bend radius. |
| **3** | Optical Splicing | Perform fusion splicing or mechanical SC/APC connector with < 0.2dB insertion loss. |
| **4** | Power Verification | Confirm received optical power at customer ATB is between -15 and -24 dBm. |
| **5** | ONT Provisioning | Register ONT Serial Number (GPON SN) on OLT and verify PON light turns solid green. |
| **6** | Customer Acceptance | Complete speed test, print sign-off report, and educate client on router LEDs. |

---

### **Footer and Supplemental Information**

*   **Grid Label:** TELEMETRY SPECTRUM ANALYSIS & FIELD DISPATCH SIGN-OFF RECORD
*   **Security Disclaimer:** TELECOM EGYPT (WE) - CONFIDENTIAL OPERATIONAL SPECIFICATION - AUTHORIZED PERSONNEL ONLY

[Binary Media: telemetry_asset_pad.dat]

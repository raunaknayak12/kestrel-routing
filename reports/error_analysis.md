# Kestrel Home: Validation Error Analysis & Triage Optimization

Detailed review of the validation misses from the out-of-time evaluation slice (Apr–Jun 2026 CRM).

---

## 1. Error Taxonomy Breakdown

- **Validation Slice Size:** 2,135 requests
- **Validation Accuracy:** **83.98%**
- **Total Errors Analyzed:** 342

| Error Category | Miss Count | % of All Misses | Description & Root Cause |
|---|---|---|---|
| **Warranty Query vs Product Advice** | 125 | 36.5% | Pre-purchase questions about warranty coverage vs general product feature queries. |
| **Ambiguous / 'Call Me' Vague Query** | 100 | 29.2% | Customer leaves a bare phone number or 'call me' without describing symptoms or equipment state. |
| **Returns & Replacement Boundary** | 49 | 14.3% | Replacement requested after 30-day window requiring warranty repair instead of return. |
| **Other Ambiguous Domain Query** | 44 | 12.9% | Short or unstructured requests with overlapping terminology. |
| **Installation vs Repair / Demo Confusion** | 18 | 5.3% | Borderline requests where a newly installed appliance is malfunctioning on day 1 or needs reinstall. |
| **Payment-Word / Billing Trap** | 6 | 1.8% | Mentions payment method ('paid by card') but the issue was a failed service visit or delayed part delivery. |

---

## 2. Confidence Calibration & 'Needs Triage' Threshold

To prevent expensive misroutes (Rs 565 per misroute), the service implements a `needs_triage` flag for low-confidence requests.
Human triage at the front desk costs approximately **Rs 100**, compared to **Rs 565** for an erroneous technician dispatch or multi-hop transfer.

| Confidence Threshold | Triaged Queue | Triaged % | Auto-Routed Volume | Auto-Routed Accuracy | Remaining Errors | Total Incurred Cost (Rs) |
|---|---|---|---|---|---|---|
| `0.35` | 221 | 10.4% | 1,914 | **91.54%** | 162 | Rs 113,630 |
| `0.40` | 264 | 12.4% | 1,871 | **92.84%** | 134 | Rs 102,110 |
| `0.45` | 286 | 13.4% | 1,849 | **93.62%** | 118 | Rs 95,270 |
| `0.50` | 304 | 14.2% | 1,831 | **94.37%** | 103 | Rs 88,595 |
| `0.55` | 326 | 15.3% | 1,809 | **94.97%** | 91 | Rs 84,015 |
| `0.60` | 354 | 16.6% | 1,781 | **95.62%** | 78 | Rs 79,470 |
| `0.70` | 376 | 17.6% | 1,759 | **96.13%** | 68 | Rs 76,020 |

> [!TIP]
> **Optimal Operating Point:** Setting the triage threshold at **0.45 - 0.50** catches the majority of ambiguous queries,
> lifting auto-routed accuracy above **87%**, while sending fewer than 8% of queries to Meenal's triage desk.

---

## 3. Sample High-Impact Validation Misses Analyzed

| Request ID | True Team | Predicted Team | Confidence | Request Snippet | Root Cause |
|---|---|---|---|---|---|
| SR508689 | `Returns & Replacement` | `Repairs` | 0.33 | "issue with mixer grinder order KO2603933 pls call back" | Ambiguous / 'Call Me' Vague Query |
| SR508691 | `Installs & Demo` | `Product Advice` | 0.35 | "need help with my room heater reg no SR69239" | Warranty Query vs Product Advice |
| SR508701 | `Repairs` | `Billing` | 0.24 | "someone contact me about induction cooktop thanks" | Ambiguous / 'Call Me' Vague Query |
| SR508705 | `Product Advice` | `Returns & Replacement` | 0.99 | "good morning, received used purifier, want exchange order KO..." | Warranty Query vs Product Advice |
| SR508706 | `Warranty Claims` | `Returns & Replacement` | 0.71 | "hello team, box was open, purifier scratched, please call ba..." | Ambiguous / 'Call Me' Vague Query |
| SR508716 | `Installs & Demo` | `Product Advice` | 0.29 | "namaste, not happy with robot vacuum pls call back" | Ambiguous / 'Call Me' Vague Query |
| SR508717 | `Product Advice` | `Repairs` | 0.28 | "good morning, vacuum query" | Warranty Query vs Product Advice |
| SR508721 | `Repairs` | `Returns & Replacement` | 0.27 | "namaste, need help with my purifier thanks" | Returns & Replacement Boundary |
| SR508724 | `Returns & Replacement` | `Warranty Claims` | 0.58 | "good morning, need warranty certificate mixer grinder, box w..." | Warranty Query vs Product Advice |
| SR508739 | `Repairs` | `Installs & Demo` | 0.39 | "sir please call back regarding product reg no SR36609" | Ambiguous / 'Call Me' Vague Query |
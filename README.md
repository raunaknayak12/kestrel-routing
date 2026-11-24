# Kestrel Home — Intelligent Service-Request Routing Engine

**Private repository** — customer data must not leave this repo or the engagement team (Operations Policy §10).

An offline, outcome-trained routing engine designed to replace the legacy vendor routing bot. Built to reduce customer service transfer loops, cut annual misroute costs, eliminate recurring licence fees, and provide transparent diagnostic explanations.

---

## Executive Summary & Performance

| Benchmark Metric | Legacy Routing Bot | Our Production Model | Improvement |
|---|---|---|---|
| **Accuracy vs True Resolution (`final_team`)** | **76.67%** | **83.98%** | **+7.31% absolute** |
| **Validation Misroute Rate** | 23.33% | **16.02%** | **31.3% error reduction** |
| **Agreement with Bot Labels** | 100.0% | **75.50%** | Rejects known bot errors |
| **Annual Misroute Operational Cost** | Rs 9,48,882 | **Rs 651,694** | **Rs 2,97,188 saved / yr** |
| **Annual Bot Software Licence** | Rs 3,20,000 | **Rs 0** | **Rs 3,20,000 saved / yr** |
| **Total Annual Operational Value** | — | — | **Rs 6,17,188 / year** |
| **Variable Cost per Request** | N/A | **Rs 0.00** | 100% offline scikit-learn |

---

## Quick Start (Clean Machine, No API Key Required)

```bash
# 1. Clone repository
git clone <repo-url>
cd kestrel-routing

# 2. Set up virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Run test suite
python -m pytest -v tests/test_endpoint.py

# 5. Launch web console & API service
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at `http://127.0.0.1:8000` to interact with the visual routing console.  
Interactive OpenAPI / Swagger docs are available at `http://127.0.0.1:8000/docs`.

---

## Repository Structure

```
kestrel-routing/
├── data/                       # Raw customer data (git-ignored per Policy §10)
│   ├── train.csv
│   ├── test_unlabelled.csv
│   ├── resolution_log.csv
│   ├── teams.csv
│   └── sample_submission.csv
├── src/
│   ├── clean.py                # Mojibake repair, team name mapping, text sanitizer
│   ├── features.py             # Word & char TF-IDF + domain heuristic indicators
│   ├── baseline_rules.py       # Policy §3 keyword router baseline & benchmarks
│   ├── train.py                # Time-split validation framework (Apr–Jun 2026 CRM)
│   ├── error_analysis.py       # Miss taxonomy & triage threshold optimization
│   └── predict.py              # Batch scoring -> generates predictions.csv
├── app/
│   ├── main.py                 # FastAPI service: POST /route, GET /health
│   └── static/
│       └── index.html          # Interactive diagnostic web console
├── reports/
│   ├── eda.md                  # Comprehensive exploratory data analysis
│   ├── policy_rules.md         # Operational policy §3/§4/§5 extraction
│   ├── error_analysis.md       # Detailed breakdown of validation misses
│   ├── validation_experiments.json # Machine-readable benchmark results
│   └── EVIDENCE.md             # Formal evidence report for leadership
├── tests/
│   └── test_endpoint.py        # Pytest integration & policy regression tests
├── model.joblib                # Serialized production pipeline (0.59 MB)
├── predictions.csv             # Scored test set (2,178 rows, verified schema)
├── MEMO.md                     # 1-page non-technical executive memo for Ritu
├── requirements.txt            # Pinned lightweight dependencies
└── README.md
```

---

## Key Strategic Decisions

| # | Decision | Strategic Justification |
|---|---|---|
| **D1** | **Train on `final_team`, not `team_label`** | `team_label` equaled initial bot assignment 100% of the time, and was correct only 77.2% of the time. Matching it at 90% would copy the bot's mistakes. |
| **D2** | **Predict current post-Jan-2026 team names** | `Installations` $\rightarrow$ `Installs & Demo`, `Consumables` $\rightarrow$ `Filters & Consumables`. All test rows postdate the rename. |
| **D3** | **Validate by time (Apr–Jun 2026 CRM slice)** | Out-of-time validation mirrors production test distribution and avoids flattering random splits. |
| **D4** | **Zero paid APIs in core path** | Fixed runtime cost: Rs 0.00 / request. Fully reproducible offline. |
| **D5** | **Honest ambiguity ceiling & triage queue** | ~4.7% of requests lack diagnostic symptoms. Requests under 45% confidence are flagged `needs_triage: true`. |
| **D6** | **Repair mojibake & deduplicate** | Eliminates legacy Zoho encoding artifacts without overfitting to noise. |

---

## API Specification

### `POST /route`
Route an incoming ticket with full diagnostic reasoning.

**Request Payload:**
```json
{
  "request_text": "I already paid via UPI for the installation visit but technician did not arrive",
  "channel": "whatsapp",
  "product_family": "Water Purifier",
  "warranty_status": "in_warranty"
}
```

**Response:**
```json
{
  "predicted_team": "Installs & Demo",
  "confidence": 0.8842,
  "needs_triage": false,
  "top3": [
    {"team": "Installs & Demo", "confidence": 0.8842},
    {"team": "Repairs", "confidence": 0.0631},
    {"team": "Billing", "confidence": 0.0215}
  ],
  "reasons": [
    "Customer mentioned payment method in passing (Policy §3: not Billing unless payment itself is disputed).",
    "New product onboarding / installation keywords: install → Installs & Demo.",
    "High-confidence match (88.4%) for queue: Installs & Demo."
  ]
}
```

### `GET /health`
Validates model artifact integrity and active configuration.

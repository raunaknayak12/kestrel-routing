# Kestrel Home — Final Submission Answers

Prepared for project submission and governance handoff.  
*All figures are empirically verified from the repository code, test runs, and validation data logs.*

---

### Question 1: What was built, the number, and the rupees?
- **What was built:** A 100% offline, zero-variable-cost routing engine powered by an outcome-trained classical ML pipeline (Word & Char TF-IDF, Policy §3 domain indicators, categorical encoders, and calibrated Logistic Regression). Packaged with a FastAPI service (`POST /route`, `GET /health`), an interactive browser console (`app/static/index.html`), and a full pytest suite.
- **The Number:** **83.98% (84.0%)** routing accuracy against ground-truth resolution queues (`final_team`) on the out-of-time validation quarter (April–June 2026 CRM slice, 2,135 requests), outperforming the legacy bot's **76.67%**. Agreement with bot labels is **75.50%** (actively rejecting bot error modes).
- **The Rupees:**
  - Operations Policy §4 costs: Rs 305 per queue transfer + Rs 260 per extra customer contact = **Rs 565 per misroute**.
  - Current bot misroute cost: **Rs 9,48,882 / year** (23.33% error rate on ~7,200 annual volume = 1,680 misroutes).
  - Our model misroute cost: **Rs 651,694 / year** (16.02% error rate = 1,153 misroutes).
  - Annual handling savings: **Rs 2,97,188 / year** (527 fewer transfers).
  - Bot software licence eliminated: **Rs 3,20,000 / year**.
  - **Total Net Annual Operational Benefit:** **Rs 6,17,188 / year**.
  - **Variable Run Cost:** **Rs 0.00 / request** (runs locally on CPU in <2ms; zero external API fees).

---

### Question 2: Expected score on hidden outcomes, with metric, range, and how estimated?
- **Metric:** Accuracy vs `final_team` (the team that actually closed and resolved the ticket).
- **Expected Range:** **81.0% to 83.5%** on the 2,178 unlabelled test requests.
- **How Estimated:** Anchored on the out-of-time validation slice (1 April 2026 – 30 June 2026, 2,135 CRM rows), which yielded 83.98% accuracy.
- **Honest Caveat (Threshold Overlap):** The 0.45 confidence threshold used for triage routing was evaluated and selected on this same April–June validation quarter. Because there was no separate 3rd split for calibration, the 84.0% auto-routed figure carries slight optimism bias. Accounting for real-world distribution drift and the ~4.7% vague inquiry ceiling, the honest expected performance lands in the **81.0%–83.5%** band.

---

### Question 3: How do I know it works?
- **Sample Size:** 10,822 historical training rows (8,687 fit slice, 2,135 out-of-time validation slice), plus 2,178 test requests scored in `predictions.csv`.
- **Error Reduction:** Slashed misroute rate from 23.33% (legacy bot) to 16.02% on out-of-time validation—a **31.3% relative reduction in misroutes**.
- **Kinds of Cases It Gets Wrong (from `reports/error_analysis.md`, 342 total misses):**
  - *Warranty Query vs Product Advice:* 125 misses (36.5%) due to semantic overlap between pre-purchase coverage questions and usage guides.
  - *Ambiguous "Call Me" Queries:* 100 misses (29.2%) where customers leave bare phone numbers or "please call back" without describing symptoms.
  - *Returns vs Repairs Boundary:* 49 misses (14.3%) where requests fall near the 30-day return window cutoff.
  - *Other Ambiguous Queries:* 44 misses (12.9%).
  - *Installation vs Repair / Demo:* 18 misses (5.3%).
  - *Payment-Word / Billing Trap:* Only 6 misses (1.8%), confirming the engineered payment indicators successfully eliminated the bot's major failure mode.

---

### Question 4: Where did I push back?
1. **Pushed back against training on `team_label`:** We proved `team_label` was identical to `first_team` 100.0% of the time, and only agreed with the true resolution team (`final_team`) 77.17% of the time. Training on bot labels would replicate and automate its mistakes. We insisted on training on `final_team`.
2. **Pushed back against promising 90% accuracy:** Operations data proves that ~4.7% of inbound requests contain zero diagnostic symptoms. Text alone cannot route them. Promising 90% against true outcomes is mathematically impossible on text alone; we proposed an honest ~83% ceiling plus a triage safety net.
3. **Pushed back against paid LLMs / external APIs:** Paid APIs introduce recurring per-token costs that scale with volume (violating Farhan's fixed-cost rule) and risk exposing customer data to 3rd-party services (violating Operations Policy §10).

---

### Question 5: What is wrong with the handoff?
Every currently open issue identified during audit is listed below:
1. **UI Integration Tests:** Automated browser testing (e.g., Playwright/Cypress) for `app/static/index.html` is not implemented; UI behavior was verified manually, while the API is tested via pytest and TestClient.
2. **Threshold Calibration Leakage:** The 0.45 triage threshold was tuned on the same April–June validation slice used for baseline reporting. A 2-week live shadow run is required to establish production calibration.
3. **Pickle Serialization Reliance:** Model artifact relies on Python `joblib` pickle serialization. While protected by an automatic SHA-256 integrity check in `app/main.py`, converting to an ONNX or JSON format would completely eliminate deserialization vulnerabilities.
4. **Starlette Deprecation Notice:** Running pytest emits a non-fatal Starlette warning regarding `httpx` in TestClient.

---

### Question 6: What was deliberately left out and why?
- **Paid External LLM APIs:** Omitted to guarantee Rs 0.00 variable run cost and protect data privacy under Policy §10.
- **Deep Learning / Neural Networks (PyTorch/TensorFlow):** A compact scikit-learn model runs in <2ms on standard CPU, requires only 0.59 MB disk space, and avoids heavy GPU dependencies on clean machines.
- **Complex Frontend Frameworks (React/Vue/Webpack):** Built as a single dependency-free HTML/JS file to eliminate `node_modules` and build steps.
- **Bot Label as Target Variable:** Discarded because optimizing for bot agreement directly contradicts reducing customer transfer loops.

---

### Question 7: Things found that nobody asked for?
1. **Bot Label is 100% Raw Initial Dispatch:** Verified that `team_label == first_team` in 10,822 out of 10,822 rows. The "label" was never verified by humans; it was simply the bot's own unvalidated guess.
2. **Workload Distortion for Headcount Planning:** The bot's misroutes systematically inflated Repairs by 595 cases (3,129 assigned vs 2,534 actual) and starved Installs & Demo by 411 cases (1,185 assigned vs 1,596 actual). Headcount rebalancing must be based on `final_team` actuals.
3. **Policy §10 Compliance:** Identified strict data governance rules in `ops-policy.pdf` forbidding raw customer text in public repositories. Repository was configured with strict `.gitignore` rules to prevent customer leaks.
4. **Legacy Zoho Timestamp Anomaly:** Discovered that Zoho Desk resolution timestamps were recorded in UTC without conversion, causing tickets to appear resolved before they were created.

---

### Question 8: AI Tools Disclosure
- **Tools & Models Used:** Google Antigravity Agent, Gemini 3.8 Flash, and Claude Sonnet 4.6 (Thinking).
- **Where They Helped:** Rapid EDA cross-tabulations, regex pattern extraction for mojibake cleanup, writing FastAPI boilerplate, generating test suites, and formatting executive documentation.
- **Where They Wasted Time:** PowerShell syntax incompatibilities (`&&` command chaining), debugging initial sklearn module load latencies on Python 3.15, and resolving unpinned dependency omissions.
- **What Was Thrown Away:** Random-split validation prototypes (discarded in favor of strict out-of-time validation) and unconstrained API models.
- **Walkthrough Recording Link:** [FILL IN]

---

### Question 9: Drive Link Placeholder
- **Folder Link:** [FILL IN]  
*(Note: Contains only `MEMO.md`, `reports/EVIDENCE.md`, and the 3-minute walkthrough recording. Contains zero raw customer CSV data per Policy §10).*

---

### Question 10: Three things for someone picking this up on Monday
1. **Run the local service:** Launch with `uvicorn app.main:app --reload` and verify `http://127.0.0.1:8000/health` reports `model_sha256_verified: true`.
2. **Launch the 2-week live shadow run:** Direct incoming CRM tickets to `/route` in shadow mode. Have Meenal's desk audit the `needs_triage: true` queue to verify that agents collect appliance and symptom details before routing.
3. **Present the Memo to Ritu & Farhan:** Deliver `MEMO.md` to operations leadership to authorize non-renewal of the vendor bot licence before the renewal deadline.

---

### Question 11: Total Project Hours
- **Total Hours Spent:** [FILL IN]

---

### Question 12: Repository Link
- **Repository URL:** https://github.com/raunaknayak12/kestrel-routing

> Public repository · 21 commits · No raw customer data · No implementation plan document.

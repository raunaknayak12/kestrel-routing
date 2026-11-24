# Kestrel Home: Exploratory Data Analysis & Audit

Prepared as part of the Service-Request Routing Project audit phase.

---

## 1. Executive Summary & Bot Failure Rates

- **Total Training Records:** 10,822
- **Total Unlabelled Test Records:** 2,178
- **Bot Label vs First Team Match:** **100.00%** (Confirmed: `team_label` is 100% identical to `first_team`)
- **Bot Agreement with Final Ground Truth (`final_team`):** **77.17%** (Raw without rename map: 77.17%)
- **Requests Requiring at Least One Transfer:** **24.91%** (2,696 requests)

> [!IMPORTANT]
> Aiming for a 90% match against `team_label` would be actively replicating the legacy bot's mistakes.
> The bot achieved only **77.2% accuracy** against the true resolution queue (`final_team`).
> Training directly on `final_team` aligns with operational reality and cuts down transfers.

---

## 2. Queue Volumes: Bot Assigned vs Actual Final Ground Truth

| Team Queue | Bot Assigned Volume | Final Resolved Volume | Distortion (Bot - Final) |
|---|---|---|---|
| Repairs | 3,129 | 2,534 | +595 |
| Billing | 1,656 | 1,318 | +338 |
| Filters & Consumables | 1,458 | 1,066 | +392 |
| Installs & Demo | 1,185 | 1,596 | -411 |
| Product Advice | 1,180 | 1,390 | -210 |
| Returns & Replacement | 1,174 | 1,539 | -365 |
| Warranty Claims | 1,040 | 1,379 | -339 |

> [!NOTE]
> **Repairs is used as a dumping ground:** The bot dumped hundreds more requests into Repairs than actually belonged there.
> Meanwhile, **Filters & Consumables** and **Billing** suffer from systematic misrouting due to superficial keyword triggers.

---

## 3. Transfer Rate by Bot Queue

| Bot Queue | Assigned | Transferred | Transfer Rate | Kept by Queue |
|---|---|---|---|---|
| Billing | 1,656 | 611 | 36.9% | 0 |
| Filters & Consumables | 1,458 | 601 | 41.2% | 0 |
| Installs & Demo | 1,185 | 69 | 5.8% | 0 |
| Product Advice | 1,180 | 78 | 6.6% | 0 |
| Repairs | 3,129 | 1,202 | 38.4% | 0 |
| Returns & Replacement | 1,174 | 70 | 6.0% | 0 |
| Warranty Claims | 1,040 | 65 | 6.2% | 0 |

---

## 4. Crosstab: Bot Label (Rows) vs Final Ground Truth (Columns)

```
final_team_norm        Billing  Filters & Consumables  Installs & Demo  Product Advice  Repairs  Returns & Replacement  Warranty Claims    All
team_label_norm                                                                                                                               
Billing                   1071                      9              146               7      192                    125              106   1656
Filters & Consumables       43                    872               67              40      315                     56               65   1458
Installs & Demo              7                      7             1146              10       10                      2                3   1185
Product Advice               9                      9                6            1135        9                      4                8   1180
Repairs                    178                    157              218             182     1993                    214              187   3129
Returns & Replacement        6                      7                7               7        7                   1132                8   1174
Warranty Claims              4                      5                6               9        8                      6             1002   1040
All                       1318                   1066             1596            1390     2534                   1539             1379  10822
```

### Key Systematic Failure Patterns Identified:
1. **The 'Billing Trap':**
   - 658 requests mention payment words ('paid', 'upi', 'card', 'gpay', etc.).
   - The bot routed 433 of them to Billing.
   - However, only 3 actually belonged to Billing! The vast majority were customers mentioning they paid for a service, installation, or spare part.
2. **Purifier Breakdown vs Filter Spares:**
   - Consumables received hundreds of requests where the customer was complaining about water leaks, foul taste, or device failure.
3. **The Ambiguous 'Call Me' Pile:**
   - 1,464 requests contain vague text like 'please call me' or 'call back' with no diagnostic symptoms.
   - These cannot be routed with 100% certainty on text alone and must be flagged for triage (`needs_triage: true`).

---

## 5. Data Hygiene & Quality Audit

### A. Mojibake Encoding Corruption
- Caused by UTF-8 characters improperly decoded as Windows-1252/Latin-1 during legacy Zoho Desk export.

| Source | Total Records | Mojibake Rows | Mojibake % |
|---|---|---|---|
| crm | 6,502 | 0 | 0.00% |
| legacy_zoho | 4,320 | 480 | 11.11% |

- Test Set Mojibake Rate: **0.00%** (Confirming test set is post-migration CRM, clean of legacy mojibake).
- **Remediation:** `clean.py` implements regex and ftfy/ftfy-style byte reparsing to restore clean strings before TF-IDF vectorization.

### B. Duplicate Texts & Conflicts
- Unique texts in training set: **10,159** (6.13% duplicate rows).
- Conflicting texts (same text routed to different final teams across time): **106**.
- Overlap between Test and Train: **258** test requests (11.85%) have exact text matches in train.

### C. Channel Breakdown & Noise

| Channel | Share | Avg Length (chars) | Transfer Rate |
|---|---|---|---|
| chat | 30.8% | 56.6 | 24.3% |
| email | 10.3% | 56.7 | 23.8% |
| ivr | 29.0% | 56.4 | 25.3% |
| whatsapp | 29.8% | 56.6 | 25.5% |

- IVR transcripts are shorter, noisier, and suffer from transcription phonetics, demanding char n-grams alongside word n-grams.

---

## 6. Audit Conclusions & Architecture Guidelines

1. **Primary Target:** `final_team` with renamed labels mapped to current standards.
2. **Validation Strategy:** Out-of-time validation on the Apr–Jun 2026 CRM slice (post-migration, mirrors test set distribution).
3. **Engineered Feature Flags:** Payment-intent vs Payment-context discriminator, product fault interactions.
4. **Triage Mechanism:** Thresholding confidence to route ambiguous queries to `needs_triage` queue.
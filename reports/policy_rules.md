# Kestrel Home Operations Policy (v4.1) — Key Routing Rules & Economics

Extracted from `ops-policy.pdf` (Internal D2C Operations Policy).

---

## 1. Routing Rules & Queue Responsibilities (§3, §5)

### Core Principle
- Inbound requests enter via IVR, chat, WhatsApp, or email.
- The vendor routing bot assigned requests at creation (`team_label` / `first_team`).
- When misrouted, agents transfer the request to the correct team. The team that closes the request is the ground truth (`final_team`).

### Policy §3: The Billing Trap
> **Critical Rule:** A request belongs to **Billing** *only when the problem is the payment itself* (invoice, GST, double charge, refund of a payment, EMI conversion).
> A customer merely mentioning that they have paid (e.g., "paid via UPI", "paid for installation") does **not** make it a billing request.

### Policy §5: Team Renaming (Effective 15 Jan 2026)
- **Installations** $\rightarrow$ **Installs & Demo**
- **Consumables** $\rightarrow$ **Filters & Consumables**
- *Responsibilities did not change.*
- All test rows (July–Sept 2026) postdate this rename. Therefore, models must output the current 7 team names.

### Current 7 Valid Teams
1. **Installs & Demo**: New-product installation, demo and wall-mounting visits.
2. **Repairs**: Product faults, breakdowns, error codes, noise, leaks — anything requiring a technician to fix.
3. **Filters & Consumables**: Filters, candles, membranes, jars, brushes, blades, AMC kits — selling and fitting spares. (Not faults).
4. **Billing**: Invoices, GST, double charges, refunds of payments, EMI conversion, coupons. Only when the payment *is* the problem.
5. **Returns & Replacement**: Damaged, wrong or incomplete deliveries; returns and exchanges within the return window.
6. **Warranty Claims**: Warranty and Kestrel Shield registration, coverage questions, claim status.
7. **Product Advice**: Pre- and post-purchase usage questions. No fault reported.

---

## 2. Economics & Decision Costs (§4)

| Parameter | Unit Cost | Notes |
|-----------|-----------|-------|
| Transfer handling time | **Rs 305** | Per transfer between teams |
| Extra customer contact | **Rs 260** | Per misroute (customer follows up) |
| **Total Misroute Cost** | **Rs 565** | **Rs 305 + Rs 260 per misrouted request** |
| Technician visit | Rs 540 | Dispatched by Repairs / Installs |
| Vendor routing bot licence | **Rs 3,20,000 / year** | Fixed recurring software cost |

### Misroute Economic Formula
For annual request volume $V$ and error rate $E$:
$$\text{Annual Misroute Cost} = V \times E \times \text{Rs } 565$$

If $V \approx 7,200$ requests/year and error rate is $22.8\%$ (bot misroutes $1 - 0.772 = 22.8\%$):
$$\text{Current Bot Misroute Cost} = 7,200 \times 0.228 \times 565 \approx \mathbf{\text{Rs } 9,27,504 \text{/year}}$$

Combined with licence (Rs 3,20,000), the bot is costing Kestrel **over Rs 12.4 lakh annually**.

---

## 3. Systems, Timestamps, and Migrations (§9)
- Before 1 Oct 2025: Legacy Zoho Desk (`legacy_zoho`).
- From 1 Oct 2025 onwards: Kestrel CRM (`crm`).
- Legacy Zoho resolution timestamps were stored in UTC without IST conversion.
- Test set (1 Jul 2026 – 30 Sep 2026) is entirely in CRM.
- Validation must be performed on the CRM time slice (Apr–Jun 2026) to reflect test conditions.

---

## 4. Data Governance (§10)
- Customer and operational data must not be uploaded to public repositories or shared outside the engagement team.
- Private repository required; raw data git-ignored; only scrubbed `predictions.csv` and aggregate metrics committed.

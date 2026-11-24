# Memorandum: Service-Request Routing Bot Replacement & Headcount Rebalancing

**To:** Ritu Deshpande, Head of D2C Operations  
**Cc:** Farhan Sheikh (Finance Controller), Meenal Joshi (Service Desk Manager), Tanmay Kulkarni (IT)  
**From:** Kabir Nanda & Analytics Engineering Team  
**Date:** 24 November 2026  
**Subject:** Service-Request Routing Bot Replacement & Headcount Rebalancing  

---

### 1. The Decision
**Do not renew the vendor routing bot licence.** However, **do not require 90% agreement with the bot’s historical labels** as the exit criterion. 

The vendor bot achieved only **77.2% accuracy** against the actual team that resolved the issue (`final_team`). In 100% of cases, the bot's label was just the initial queue where the ticket landed, and nearly **25% of all inbound requests required costly manual transfers**. Forcing a new model to match the bot at 90% would simply automate and perpetuate its systematic mistakes: dumping purifier leaks into Consumables, sending installation queries to Billing because someone typed "UPI", and using Repairs as a default dumping ground.

Instead, we have deployed an offline, outcome-trained routing model trained directly on the resolution ground truth.

---

### 2. The Number
On the most recent out-of-time validation quarter (April–June 2026, CRM post-migration):
- **Our Model Accuracy against True Resolution:** **84.0%** (vs the legacy bot's **76.7%**).
- **Agreement with Legacy Bot:** **75.5%** (demonstrating that the model actively corrects the bot's known errors).
- **The Ambiguity Ceiling:** ~4.7% of customer messages are vague requests (e.g., *"call me"*, *"urgent call back"*) containing zero diagnostic details. No AI model can route these reliably from text alone.
- **Triage Safety Net:** The model flags these low-confidence requests (< 45% confidence) as `needs_triage: true` (approx. 13% of volume) for Meenal’s intake desk, preventing misdirected dispatches.

---

### 3. The Rupees
Under operations policy §4, each misroute costs **Rs 565** (Rs 305 handling time + Rs 260 extra customer contact):

1. **Misroute Reductions:** Our model cuts the misroute rate from 23.3% to 16.0%, eliminating over **520 unnecessary transfers annually**, saving **Rs 2.97 Lakh per year**.
2. **Licence Elimination:** Dropping the third-party routing bot licence saves **Rs 3.20 Lakh per year**.
3. **Variable Operating Cost:** **Rs 0.00 / month.** The solution runs 100% offline using a compact 0.59 MB classical ML pipeline. Farhan can bank the entire **Rs 6.17 Lakh annual net benefit** without ongoing cloud API bills.

---

### 4. What to Do Next Week
1. **Shadow Run (2 Weeks):** Run the new model in shadow mode alongside the bot on live CRM tickets. Have Meenal verify that Billing and Consumables queues see immediate relief from misroutes.
2. **Staff Meenal's Triage Queue:** Route requests flagged with `needs_triage: true` to a rapid-triage intake screen where agents ask one clarifying question (*"Which appliance, and what symptoms are you seeing?"*).
3. **Rebalance Team Headcount:** Historical bot data falsely inflated Repairs by ~600 tickets while starving Installs & Demo (-411 tickets) and Returns (-365 tickets). Reallocate 2–3 agent roles from Repairs to Installs & Demo and Returns to match true resolution workloads.
4. **Terminate Bot Contract:** Formal notice of non-renewal can be issued ahead of the licence expiration.

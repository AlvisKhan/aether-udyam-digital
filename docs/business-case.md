# Udyam Digital — Team Aether, NIT Silchar

## Problem and first customer

The fictional acquisition funnel activates 368 of 5,000 leads (7.36%). Needs-assessed leads fall from 1,974 to 861 quote acceptances: a loss of 1,113. Owner-facing price clarity, faster quotes and fewer KYC rework loops are the intervention points.

Professional offices are the proposed first segment: 138 activations from 1,247 leads (11.07%), observed blended CAC ₹10,694.71, mean activation time 16.92 days and 3.07 follow-up calls per activated customer. Compared with micro retail, they show stronger conversion and lower CAC in this synthetic sample. That is a prioritisation hypothesis, not a causal estimate.

## Value and pricing

An owner describes their business in English or Hindi. Gemini extracts structured requirements. Server rules check city tier, employee/site thresholds, GST eligibility, contract lengths and product dependencies before calculating the quote. Ambiguous backup requests ask for clarification. The owner edits quantities and add-ons before local KYC checks and simulated order tracking.

Worked clinic bundle: one P02 Biz Fibre 300 at ₹1,499/month and five P16 email seats at ₹125/month = ₹2,124/month before taxes. Setup is zero and the minimum term is twelve months. Activation is estimated from the slowest included catalogue product, subject to serviceability. These are synthetic catalogue prices, not actual Airtel offers.

## Pilot hypotheses and measurement

Use a matched professional-office control group with the same channel mix, eligibility and observation window. Predefine the sample size and power calculation before launch; 1,000 leads below is only a financial sensitivity example.

| KPI | Synthetic professional-office baseline | Pilot target |
|---|---:|---:|
| Lead-to-activation | 11.07% | 15% |
| Blended CAC | ₹10,695 | ₹8,500 |
| Mean lead-to-activation | 16.9 days | 10 days |
| Follow-up calls per activated owner | 3.1 | 1 |

Targets are not achieved outcomes. Include cloud inference, document processing, servicing and partner costs in pilot CAC. Measure six-month churn only after a full follow-up window. Do not target individual leads with the dataset's synthetic forward-looking churn field.

At 1,000 eligible leads, moving from 138/1247 activation to 15% produces 39.33 additional activations. If all incremental customers take the ₹2,124 example bundle, additional monthly revenue is about ₹83,543, rounded to ₹83k in the deck. This is before churn, discounts, gross margin, fulfilment and fixed costs. It is not forecast profit or ROI; changing product mix changes revenue materially.

## Rollout and role of partners

Days 1–30: sandbox evaluation, owner usability research and partner training. Define serviceability handoff and exception ownership. Days 31–60: controlled pilot with human-assisted resolution of uncertain documents, unavailable products and unsuitable budgets. Days 61–90: expand only after conversion, CAC and activation metrics improve without worse quality/churn indicators.

Keep existing field/channel attribution for partner-originated leads. Route unresolved advisory/KYC cases back to partners. Test activation- and service-quality-based incentives rather than rewarding volume alone. This operating model is a proposal: no partner dashboard, routing integration or commission system is implemented in the prototype.

## Main risks

Model misclassification: schema validation, clarification, catalogue rules and guided fallback. OCR uncertainty: fail to review instead of guessing. Privacy: separate AI/KYC consent, minimum data, local document processing, masked displays and expiring sessions; Gemini free-tier disclosure. Delivery risk: no instant physical-installation promise; real serviceability/fulfilment integrations are future work. Channel conflict: attribution and assisted-case ownership need pilot validation.

Sources: supplied Airtel_SYNC_Case.pdf; product_catalogue.csv; smb_leads.csv; reproducible scripts/analyse.py; docs/verification.md. Competitor research is in competitor-research.md.

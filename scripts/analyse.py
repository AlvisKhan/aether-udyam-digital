"""Reproducible descriptive analysis; no invented forecasts or real Airtel figures."""
import sys,json,csv,statistics,collections
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((root/'data/smb_leads.csv').open()))
activated=[x for x in rows if x['outcome']=='Activated']
stages=['Lead','Contacted','Needs assessed','Quote accepted','KYC complete','Activated']
counts={stage:sum(stages.index(x['stage_reached'])>=i for x in rows) for i,stage in enumerate(stages)}
segments=[]
for name in sorted({x['segment'] for x in rows}):
    a=[x for x in rows if x['segment']==name];b=[x for x in a if x['outcome']=='Activated']
    segments.append({'segment':name,'leads':len(a),'activated':len(b),'activation_rate':round(100*len(b)/len(a),2),
        'mean_mrr':round(statistics.mean(float(x['monthly_bundle_value_inr']) for x in b)),
        'cac':round(sum(float(x['acquisition_cost_inr']) for x in a)/len(b)),
        'churn_rate':round(100*sum(x['churned_within_6_months']=='Y' for x in b)/len(b),2)})
quote_barriers=collections.Counter(x['drop_reason'] for x in rows if x['stage_reached']=='Needs assessed' and x['outcome']=='Dropped')
d={'scope':'Apr–Jun 2026 · 5,000 supplied synthetic small-business leads','leads':len(rows),'activated':len(activated),
   'activation_rate':round(100*len(activated)/len(rows),2),'activation_days':round(statistics.mean(float(x['days_lead_to_activation']) for x in activated),1),
   'cac':round(sum(float(x['acquisition_cost_inr']) for x in rows)/len(activated)),
   'follow_up_calls':round(statistics.mean(float(x['customer_follow_up_calls']) for x in activated),1),
   'funnel':counts,'segments':segments,'quote_barriers':[{'reason':k,'count':v} for k,v in quote_barriers.most_common()],
   'drop_reasons':dict(collections.Counter(x['drop_reason'] for x in rows if x['outcome']=='Dropped'))}
(root/'public/insights.json').write_text(json.dumps(d,indent=2,ensure_ascii=False))
lines=['# Dataset findings','',d['scope']+'. All figures below describe the synthetic case, not Airtel performance.','',
       f"Overall activation: {len(activated)}/{len(rows)} = {d['activation_rate']}%. Mean activation: {d['activation_days']} days. Blended CAC: ₹{d['cac']:,}.",'',
       '| Segment | Leads | Activations | Conversion | Mean monthly revenue | Blended CAC | 6-month churn |',
       '|---|---:|---:|---:|---:|---:|---:|']
for s in segments: lines.append(f"| {s['segment']} | {s['leads']} | {s['activated']} | {s['activation_rate']}% | ₹{s['mean_mrr']:,} | ₹{s['cac']:,} | {s['churn_rate']}% |")
lines+=['','## Interpretation','','Professional offices are the proposed pilot segment: stronger conversion and lower observed CAC than micro retail. This is descriptive; segment mix and sales channel may confound the comparison.','',
'CAC = total acquisition cost for all leads in that segment / activated customers. MRR and churn are calculated only among activated customers. Neither revenue nor CAC includes a complete margin/cost model.','',
'## Quote barriers after needs assessment','']
for reason,count in quote_barriers.most_common(): lines.append(f'- {reason}: {count} leads')
lines+=['','## Pilot targets (hypotheses, not achieved results)','','- Professional-office activation: 11.07% → 15% in a controlled pilot. Compare matched segment and channel cohorts.','- Professional-office mean activation time: 16.9 → 10 days; respect catalogue product-specific installation times.','- Professional-office blended CAC: ₹10,695 → ₹8,500; include digital servicing and support costs.','- Professional-office follow-up calls: 3.1 → 1 per activated customer.','- Six-month churn: monitor by segment after a complete follow-up window; do not claim an early result.','',
'## Important limits','','Forward six-month churn fields extend beyond the simulated 15 July 2026 date. Use only as a synthetic retrospective illustration, never as an available real-time targeting signal. Dataset segment shares differ from the indicative market shares in the case appendix. Do not equate the two.']
(root/'docs/data-findings.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:d[k] for k in ('activation_rate','activation_days','cac','funnel','segments')},indent=2))

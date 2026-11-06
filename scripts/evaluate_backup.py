#!/usr/bin/env python3
"""Three live fictional intent checks. Run explicitly; consumes provider quota."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai_advisor import chat_turn,AIError
base={'business_type':'Clinic','segment':'prof','employees':5,'sites':1,'tier':2,'budget':1800,'term':12,'fibre':True,'needs':['internet','email']}
cases=[('Hindi network backup','मेरा बजट अभी भी 1800 रुपये प्रति माह है। इंटरनेट और पाँच लोगों के ईमेल के साथ इंटरनेट बैकअप भी जोड़ दीजिए।','network'),('Hindi file backup','पाँच लोगों के ईमेल और इंटरनेट के साथ फाइलों का क्लाउड बैकअप भी जोड़ें।','files'),('Unspecified backup','बैकअप भी जोड़ें।','ambiguous')]
print('Running three live synthetic tests; provider quota/billing rules apply.',flush=True)
for name,message,kind in cases:
 try:r,_=chat_turn({'known':dict(base),'history':[]},message,'hi')
 except AIError as e:sys.exit(name+': provider test could not complete: '+str(e))
 ids={p['product_id'] for p in r['quote']['items']} if r['quote'] else set()
 ok=('P09' in ids and 'P17' not in ids) if kind=='network' else ('P17' in ids and 'P09' not in ids) if kind=='files' else (r['quote'] is None and r['missing']==['backup_kind'])
 print(name+': '+('PASS' if ok else 'FAIL'),flush=True)
 if not ok:sys.exit(1)

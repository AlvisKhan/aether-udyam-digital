from localization import language_code
"""Catalogue and KYC rules. Only fictional competition data is supported."""
from pathlib import Path
import csv, re, datetime, difflib, math
ROOT = Path(__file__).resolve().parent
TODAY = datetime.date(2026, 7, 15)

def read_csv(name):
    with (ROOT / 'data' / name).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

CATALOGUE = read_csv('product_catalogue.csv')
PRODUCTS = {p['product_id']: p for p in CATALOGUE}
GST = {r['gstin']: r for r in read_csv('mock_gstin_registry.csv')}
UDYAM = {r['udyam_number']: r for r in read_csv('mock_udyam_registry.csv')}

def integer(value, low, high, label):
    if isinstance(value, bool): raise ValueError(f'{label} must be a number')
    try:
        n = int(value)
        if float(value) != n: raise ValueError()
    except (ValueError, TypeError): raise ValueError(f'{label} must be a whole number')
    if not low <= n <= high: raise ValueError(f'{label} must be between {low} and {high}')
    return n

CURRENT_TOOLS={'broadband','hotspot','personal_email','business_email','billing','security','other','none','skip'}
def current_tools(value):
    if not isinstance(value,list) or len(value)>9 or any(not isinstance(x,str) or x not in CURRENT_TOOLS for x in value):
        raise ValueError('Choose valid current tools')
    value=list(dict.fromkeys(value))
    if len(value)>1 and set(value).intersection({'none','skip'}):raise ValueError('Choose none or skip separately from existing tools')
    return value

def setup_comparison(b,items):
    selected={p['product_id']:p['product_name'] for p in items}
    mapping={
      'broadband':(['P01','P02','P03','P04','P05','P06'],'internet'),
      'hotspot':(['P01','P02','P03','P04','P05','P06'],'internet'),
      'personal_email':(['P16'],'email'), 'business_email':(['P16'],'existing_email'),
      'billing':(['P19'],'billing'), 'security':(['P20'],'security')}
    rows=[]
    for tool in b.get('current_tools',[]):
        ids,reason=mapping.get(tool,([], 'unchanged'))
        products=[selected[k] for k in ids if k in selected]
        if tool in ('none','skip'):reason='new' if tool=='none' else 'unknown'
        elif not products:reason='unchanged'
        rows.append({'tool':tool,'reason':reason,'products':products})
    return rows

def profile(raw):
    segment = raw.get('segment', 'prof')
    if segment not in ('micro','prof','multi','mfg'): raise ValueError('Choose a valid business segment')
    needs = raw.get('needs', [])
    allowed = {'internet','mobile','email','backup','security','whatsapp','pos','cctv','failover','static','sdwan','iot','website','telephony'}
    if not isinstance(needs,list) or not set(needs) <= allowed: raise ValueError('Unsupported business need')
    gstin = re.sub(r'\s','',str(raw.get('gstin','')).upper())
    return {'segment':segment, 'business_type':str(raw.get('business_type','Office'))[:80],
            'employees':integer(raw.get('employees',5),1,1000,'Employees'),
            'sites':integer(raw.get('sites',1),1,50,'Locations'),
            'tier':str(integer(raw.get('tier',2),1,2,'City tier')),
            'budget':integer(raw.get('budget',5000),1,5000000,'Monthly budget'),
            'term':integer(raw.get('term',24),1,36,'Maximum contract'),
            'fibre':raw.get('fibre',True) is True, 'gstin':gstin, 'needs':needs,
            'language':language_code(raw.get('language')),'current_tools':current_tools(raw.get('current_tools',[]))}

def gst_checksum(value):
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if len(value) != 15 or any(c not in chars for c in value): return False
    total = 0
    for i,c in enumerate(value[:14]):
        n = chars.index(c) * (1 if i % 2 == 0 else 2)
        total += n // 36 + n % 36
    return chars[(36-total%36)%36] == value[-1]

def lookup_gst(value):
    value = re.sub(r'\s','',str(value).upper())
    # The pack deliberately uses X as the PAN entity character. Do not reject X.
    if not re.fullmatch(r'\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]',value) or not gst_checksum(value):
        return {'ok':False,'reason':'GSTIN format or checksum is invalid','record':None}
    record = GST.get(value)
    if not record: return {'ok':False,'reason':'Not found in the mock GST registry','record':None}
    ok = record['status'].lower()=='active'
    return {'ok':ok,'reason':'Active registration' if ok else f"Registration is {record['status']}",'record':record}

def eligible(p, business):
    problems = []
    if business['tier'] not in p['available_city_tiers'].split(';'): problems.append('Unavailable in this city tier')
    if business['employees'] < int(p['min_employees']): problems.append(f"Needs at least {p['min_employees']} employees")
    if business['sites'] < int(p['min_sites']): problems.append(f"Needs at least {p['min_sites']} locations")
    if p['requires_gstin']=='Y' and not lookup_gst(business['gstin'])['ok']: problems.append('Needs an active GSTIN')
    if int(p['min_contract_months']) > business['term']: problems.append(f"Minimum contract is {p['min_contract_months']} months")
    if p['product_id'] in ('P01','P02','P03','P05','P06') and not business['fibre']: problems.append('Requires a site feasibility check; fibre marked unavailable')
    return problems

def quantity(p,b):
    return b['sites'] if p['unit']=='per site' else b['employees'] if p['unit'] in ('per user','per device') else 1

def quote(b, items):
    if not isinstance(items,list) or not items: raise ValueError('Select at least one product')
    if len(items)>25: raise ValueError('Too many product lines')
    lines=[]; errors=[]; seen=set()
    for item in items:
        pid=item.get('id'); p=PRODUCTS.get(pid)
        if not p: raise ValueError('Unknown product')
        if pid in seen: raise ValueError('Duplicate product line')
        seen.add(pid)
        q=integer(item.get('quantity',1),1,5000,'Product quantity')
        if p['unit']=='per site' and q != b['sites']: errors.append(f"{p['product_name']}: quantity must cover all {b['sites']} locations")
        errors.extend(f"{p['product_name']}: {e}" for e in eligible(p,b))
        # Demo policy: published minimum catalogue price, no invented discounts.
        price=int(p['price_min_inr_per_month']); setup=int(p['one_time_setup_inr'])
        lines.append({**p,'quantity':q,'unit_price':price,'monthly':price*q,'setup':setup*q})
    for p in lines:
        dependencies=p['requires_one_of'].split('|') if p['requires_one_of'] else []
        if dependencies and not seen.intersection(dependencies): errors.append(f"{p['product_name']}: add a compatible internet product")
    monthly=sum(p['monthly'] for p in lines); setup=sum(p['setup'] for p in lines)
    return {'items':lines,'monthly':monthly,'setup':setup,'first_payment':monthly+setup,
            'contract':max(int(p['min_contract_months']) for p in lines),'install_days':max(int(p['typical_install_days']) for p in lines),
            'errors':errors,'valid':not errors,'within_budget':monthly<=b['budget'],
            'over_budget':max(0,monthly-b['budget']), 'tax_note':'Illustrative catalogue prices. Taxes excluded; confirm at fulfilment.',
            'price_policy':'Catalogue minimum prices; setup fees charged per purchased unit.',
            'setup_comparison':setup_comparison(b,lines)}

NEEDS={'internet':['P02','P01','P04'],'mobile':['P07'],'email':['P16'],'backup':['P17'],
       'security':['P20'],'whatsapp':['P15'],'pos':['P19'],'cctv':['P23'],'failover':['P09'],
       'static':['P11'],'sdwan':['P10'],'iot':['P24'],'website':['P18'],'telephony':['P12']}

def recommend(b):
    selected=[]; notes=[]; covered=[]
    for need in b['needs']:
        ids=list(NEEDS[need])
        if need=='internet':
            ids=(['P05','P02','P01','P04'] if b['segment']=='mfg' else ['P01','P04'] if b['segment']=='micro' else ['P02','P01','P04'])
        choices=[PRODUCTS[i] for i in ids if not eligible(PRODUCTS[i],b)]
        if not choices:
            notes.append(f"{need}: no eligible product. Check GSTIN, contract or business size."); continue
        p=choices[0]
        if p['product_id'] not in [i['id'] for i in selected]: selected.append({'id':p['product_id'],'quantity':quantity(p,b)})
        covered.append(need)
    # Add a required dependency when the user asks for a dependent product alone.
    for item in selected[:]:
        p=PRODUCTS[item['id']]; dep=p['requires_one_of'].split('|') if p['requires_one_of'] else []
        if dep and not set(dep).intersection(i['id'] for i in selected):
            candidates=[PRODUCTS[i] for i in dep if not eligible(PRODUCTS[i],b)]
            if candidates:
                base=min(candidates,key=lambda x:int(x['price_min_inr_per_month']))
                selected.insert(0,{'id':base['product_id'],'quantity':quantity(base,b)})
                notes.append(f"Added {base['product_name']} because {p['product_name']} requires it.")
            else: notes.append(f"{p['product_name']} has no eligible dependency; request assistance.")
    if not selected:
        return {'quote':None,'notes':notes or ['Choose at least one business need.'],'mode':'offline','covered':[]}
    result=quote(b,selected)
    # Cheaper compatible internet option before removing any requested capability.
    if not result['within_budget']:
        for item in selected:
            if item['id']=='P02' and not eligible(PRODUCTS['P01'],b): item['id']='P01'
        result=quote(b,selected)
    if not result['within_budget']: notes.append(f"This bundle exceeds your budget by ₹{result['over_budget']:,}/month. Remove an add-on or ask a partner for help; no requested need was silently dropped.")
    notes.append('Offline guided advisor. Generative AI is not connected in this version.')
    return {'quote':result,'notes':notes,'mode':'offline','covered':covered}

def mask(value):
    return '*'*max(0,len(value)-4)+value[-4:] if value else ''

def normal(value): return re.sub(r'[^a-z0-9]','',value.lower())

def extract_fields(text):
    def field(labels):
        for label in labels:
            m=re.search(r'(?im)^\s*'+label+r'\s*[:\-]?\s*([^\n]+)',text)
            if m:
                value=m.group(1).strip()
                # Specimen addresses wrap onto a second row, sometimes with a label.
                if 'address' in label.lower() or 'principal' in label.lower():
                    after=text[m.end():].lstrip('\n').split('\n')[0]
                    if re.match(r'(?i)(place of business|[a-z]+ Pradesh|ndhra|ashtra|\d{2,6}$|[a-z]+ - \d)',after):
                        value += ' '+re.sub(r'(?i)^place of business\s*','',after)
                return value
        return ''
    gst=re.search(r'\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b',text.upper())
    udyam=re.search(r'UDYAM-[A-Z]{2}-\d{2}-\d{7}',text.upper())
    dates=re.findall(r'\b20\d{2}-\d{2}-\d{2}\b',text)
    return {'gstin':gst.group() if gst else '', 'udyam':udyam.group() if udyam else '',
            'legal_name':field(['Legal name','Enterprise name','Business name','For business']),
            'person_name':field(['Name']),
            'address':field(['Supply address','Principal place of business','Service address','Address of principal','Address']),
            'document_date':field(['Bill date','Date of issue','Issue date']),
            'valid_until':field(['Valid till','Valid until','Expiry date']), 'designation':field(['Designation']), 'dates':dates}

def validate_kyc(documents, gstin='', udyam=''):
    checks=[]; combined={}; gst=lookup_gst(gstin) if gstin else None
    def add(ok,title,detail,severity='error'):
        checks.append({'ok':bool(ok),'title':title,'detail':detail,'severity':severity})
    if gstin: add(gst['ok'],'GST registration',gst['reason'])
    if udyam:
        reg=UDYAM.get(udyam.upper()); add(bool(reg),'Udyam registration','Found in mock registry' if reg else 'Not found in mock registry')
    if not gstin and not udyam: add(False,'Business registration','Provide GSTIN or Udyam. A missing GSTIN does not exclude products that do not require it.')
    kinds={d['kind'] for d in documents}
    add('address' in kinds,'Address proof','Document provided' if 'address' in kinds else 'Address proof required')
    add('signatory' in kinds,'Authorised signatory','Document provided' if 'signatory' in kinds else 'Signatory ID required')
    add(bool(kinds.intersection({'gst','udyam'})),'Registration document','Document provided' if kinds.intersection({'gst','udyam'}) else 'Upload a GST or Udyam certificate')
    for d in documents:
        f=extract_fields(d['text']); combined[d['kind']]=f
        add(bool(d['text'].strip()),f"{d['kind'].title()} extraction",'Text extracted locally' if d['text'].strip() else 'No text found; upload a clearer image')
        if d['kind']=='gst':
            add(bool(f['gstin']) and f['gstin']==gstin,'Certificate GSTIN match','Matches entered GSTIN' if f['gstin']==gstin and gstin else 'GSTIN missing or different from entered registration')
            if gst and gst['record'] and f['legal_name']:
                score=difflib.SequenceMatcher(None,normal(f['legal_name']),normal(gst['record']['legal_name'])).ratio()
                add(score>=.85,'Legal name match','Matches mock GST registry' if score>=.85 else 'Legal name differs; review required')
        if d['kind']=='udyam': add(bool(f['udyam']) and f['udyam']==udyam,'Certificate Udyam match','Matches entered Udyam' if f['udyam']==udyam and udyam else 'Udyam missing or different from entered registration')
        if d['kind']=='address':
            try:
                date=datetime.date.fromisoformat(f['document_date']); age=(TODAY-date).days
                add(0<=age<=90,'Address proof age',f'{age} days old; must be 0–90 days as of {TODAY}')
            except ValueError: add(False,'Address proof age','Could not extract bill date; manual review required')
        if d['kind']=='signatory':
            role=f['designation'].lower()
            add(any(x in role for x in ('owner','partner','director','proprietor')),'Signatory authority', 'Role supports authority in this specimen' if any(x in role for x in ('owner','partner','director','proprietor')) else 'Manager or employee role needs additional authorisation; manual review required')
            try:
                date=datetime.date.fromisoformat(f['valid_until']); add(date>=TODAY,'Signatory ID validity',f'Valid until {date}')
            except ValueError: add(False,'Signatory ID validity','Could not extract expiry; manual review required')
    if gst and gst['record']:
        names=[normal(gst['record']['legal_name']),normal(gst['record']['trade_name'])]
        for kind in ('signatory','udyam'):
            name=combined.get(kind,{}).get('legal_name','')
            if name:
                score=max(difflib.SequenceMatcher(None,normal(name),n).ratio() for n in names)
                add(score>=.85,f'{kind.title()} business match','Matches registration' if score>=.85 else 'Business name differs from registration')
        if gst['record']['constitution'].lower()=='proprietorship':
            person=combined.get('signatory',{}).get('person_name','')
            legal=gst['record']['legal_name'].split('(Prop.')[0].strip()
            add(bool(person) and difflib.SequenceMatcher(None,normal(person),normal(legal)).ratio()>=.9,'Proprietor name match','Signatory must match the registered proprietor; otherwise authorisation is required')
        expected=normal(gst['record']['principal_place_of_business'])
        addr=combined.get('address',{}).get('address','')
        if addr:
            score=difflib.SequenceMatcher(None,normal(addr),expected).ratio()
            add(score>=.85,'Business address match','Matches registry' if score>=.85 else 'Address differs from registry; review required')
        else: add(False,'Business address match','Address not extracted; review required')
    # This prototype cannot establish real-world signatory authority or authenticity.
    add(True,'Verification boundary','Format, date and cross-document checks only. Real identity, authority and authenticity require authorised provider verification.','info')
    return {'ok':all(c['ok'] for c in checks if c['severity']=='error'),'checks':checks,
            'extracted':{k:{**v,'gstin':mask(v['gstin']),'udyam':mask(v['udyam'])} for k,v in combined.items()},
            'as_of':str(TODAY)}

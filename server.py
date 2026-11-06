#!/usr/bin/env python3
"""Offline prototype server. Bind to loopback; no customer data leaves this process."""
import base64, datetime, hashlib, http.cookies, json, mimetypes, os, re, secrets, shutil, subprocess, tempfile, time, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
from core import ROOT, PRODUCTS, GST, UDYAM, TODAY, profile, recommend, quote, eligible, lookup_gst, validate_kyc, mask
from config import ai_status
from ai_advisor import chat_turn, AIError
SESSIONS = {}
AI_LOCK=threading.Lock()
OCR_CACHE = {}
CACHE = ROOT/'data/ocr_cache.json'
if CACHE.exists(): OCR_CACHE = json.loads(CACHE.read_text())
OCR_BINARY=ROOT/'.runtime/ocr'

def ocr(data):
    digest=hashlib.sha256(data).hexdigest()
    if digest in OCR_CACHE: return OCR_CACHE[digest]['text'], 'local OCR (cached extraction)'
    if not (ROOT/'node_modules/tesseract.js').exists(): raise ValueError('Run npm install to enable local OCR for new images. Supplied specimens use cached actual OCR.')
    with tempfile.TemporaryDirectory(prefix='udyam-') as tmp:
        path=Path(tmp)/'document.png'; path.write_bytes(data)
        from image_clean import clean
        cleaned=Path(tmp)/'clean.png'; clean(path,cleaned)
        result=subprocess.run(['node',str(ROOT/'scripts/ocr.cjs'),str(cleaned)],capture_output=True,text=True,timeout=25)
        if result.returncode: raise ValueError('Could not read image. Upload a clear PNG or JPEG.')
        return result.stdout.strip(), 'local Tesseract OCR'

def safe_result(result):
    # Full extracted fields and document text never enter browser logs or order records.
    return result

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def session(self):
        cookie=http.cookies.SimpleCookie(self.headers.get('Cookie',''))
        sid=cookie.get('udyam_session'); sid=sid.value if sid else ''
        now=time.time()
        for key in list(SESSIONS):
            if now-SESSIONS[key]['seen']>1800: del SESSIONS[key]
        if sid not in SESSIONS:
            sid=secrets.token_urlsafe(32); SESSIONS[sid]={'seen':now,'csrf':secrets.token_urlsafe(24),'consent':False,'docs':[]}
        self.sid=sid; SESSIONS[sid]['seen']=now
        return SESSIONS[sid]
    def send(self,data,status=200,kind='application/json'):
        raw=json.dumps(data,ensure_ascii=False).encode() if kind=='application/json' else data
        self.send_response(status); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if hasattr(self,'sid'): self.send_header('Set-Cookie',f'udyam_session={self.sid}; HttpOnly; SameSite=Strict; Path=/; Max-Age=1800')
        self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        try:
            path=urlsplit(self.path).path; s=self.session()
            if path=='/api/bootstrap':
                self.send({'csrf':s['csrf'],'mode':'hybrid' if ai_status()['configured'] else 'offline','ai':{**ai_status(),'consent':s.get('ai_consent',False)},'as_of':str(TODAY),'ocr_ready':bool(OCR_CACHE) or (ROOT/'node_modules/tesseract.js').exists(),
                           'catalogue':list(PRODUCTS.values()),'order':s.get('order'), 'consent':s['consent']}); return
            if path=='/api/order': self.send({'order':s.get('order')}); return
            if path=='/api/insights': self.send(json.loads((ROOT/'public/insights.json').read_text())); return
            if path.startswith('/api/specimen/'):
                name=path.rsplit('/',1)[-1]
                if not re.fullmatch(r'K(0[1-9]|1[0-2])',name): raise ValueError('Unknown specimen')
                docs=[]; gstin=''; udyam=''
                for f in sorted((ROOT/'data/kyc_documents').glob(name+'_*.png')):
                    text,method=ocr(f.read_bytes())
                    kind='gst' if 'gst_certificate' in f.name else 'udyam' if 'udyam_certificate' in f.name else 'address' if 'address' in f.name else 'signatory'
                    docs.append({'kind':kind,'text':text,'source':f.name,'method':method})
                    if kind=='gst':
                        from core import extract_fields
                        gstin=extract_fields(text)['gstin']
                    if kind=='udyam':
                        from core import extract_fields
                        udyam=extract_fields(text)['udyam']
                # Specimens are fictional. Send identifiers only after consent.
                if not s['consent']: raise ValueError('Give KYC consent before loading a specimen')
                s['docs']=docs; s.pop('kyc',None)
                self.send({'documents':[{'kind':d['kind'],'source':d['source'],'method':d['method']} for d in docs], 'gstin':gstin,'udyam':udyam}); return
            if path.startswith('/api/'): self.send({'error':'Not found'},404); return
            if path=='/': path='/index.html'
            target=(ROOT/'public'/path.lstrip('/')).resolve()
            if not target.is_relative_to((ROOT/'public').resolve()) or not target.is_file(): self.send({'error':'Not found'},404); return
            if target.suffix=='.json':self.send(json.loads(target.read_text()))
            else:self.send(target.read_bytes(),kind=mimetypes.guess_type(target)[0] or 'application/octet-stream')
        except (ValueError,RuntimeError) as e: self.send({'error':str(e)},400)
        except Exception: self.send({'error':'Could not complete this request. Try again.'},500)
    def do_POST(self):
        try:
            s=self.session(); origin=self.headers.get('Origin')
            if origin and origin not in (f'http://localhost:{self.server.server_port}',f'http://127.0.0.1:{self.server.server_port}'): self.send({'error':'Origin not allowed'},403); return
            if self.headers.get('X-CSRF-Token') != s['csrf']: self.send({'error':'Session expired; refresh the page'},403); return
            length=int(self.headers.get('Content-Length',0))
            if not 0<length<6500000: raise ValueError('Request too large or empty')
            body=json.loads(self.rfile.read(length)); path=urlsplit(self.path).path
            if path=='/api/reset':
                epoch=s.get('ai_epoch',0)+1;s.clear(); s.update({'ai_epoch':epoch,'seen':time.time(),'csrf':secrets.token_urlsafe(24),'consent':False,'docs':[]}); self.send({'ok':True}); return
            if path=='/api/ai/consent':
                s['ai_consent']=body.get('consent') is True
                if not s['ai_consent']:
                    s.pop('ai_state',None)
                    s['ai_epoch']=s.get('ai_epoch',0)+1
                self.send({'ok':True,'consent':s['ai_consent']});return
            if path=='/api/ai/reset':
                s.pop('ai_state',None);s['ai_epoch']=s.get('ai_epoch',0)+1
                self.send({'ok':True});return
            if path=='/api/ai/chat':
                if not s.get('ai_consent'):raise ValueError('Agree to AI processing before sending a message, or use guided questions.')
                if not ai_status()['configured']:raise AIError('AI is not connected yet. Run python3 scripts/setup_ai.py locally and restart the server, or use guided questions.')
                with AI_LOCK:
                    if s.get('ai_busy'):raise ValueError('The advisor is still answering your previous message.')
                    calls=[x for x in s.get('ai_calls',[]) if time.time()-x<60]
                    if len(calls)>=12:raise ValueError('Please wait a minute before sending more AI messages.')
                    calls.append(time.time());s['ai_calls']=calls;s['ai_busy']=True
                epoch=s.get('ai_epoch',0)
                try:
                    result,state=chat_turn(s.get('ai_state',{}),body.get('message'),body.get('language','en'),s.get('profile',{}).get('gstin',''))
                    if not s.get('ai_consent') or s.get('ai_epoch',0)!=epoch:raise ValueError('The conversation was cleared. Start a new message.')
                    s['ai_state']=state
                    s.pop('kyc',None);s.pop('order',None);s.pop('quote',None)
                    if result.get('profile') and result.get('quote'):
                        s['profile']=profile({**result['profile'],'gstin':s.get('profile',{}).get('gstin','')})
                        s['quote']=result['quote'];s.pop('order',None);s.pop('kyc',None)
                    self.send(result);return
                finally:s['ai_busy']=False
            if path=='/api/recommend':
                b=profile(body); result=recommend(b); s['profile']=b; s['quote']=result.get('quote');s.pop('order',None)
                self.send(result); return
            if path=='/api/quote':
                if 'profile' not in s: raise ValueError('Complete business questions first')
                result=quote(s['profile'],body.get('items',[])); s['quote']=result; s.pop('order',None); self.send(result); return
            if path=='/api/consent':
                s['consent']=body.get('consent') is True
                if not s['consent']:
                    s['docs']=[];s.pop('kyc',None);s.pop('order',None)
                    if s.get('profile'): s['profile']['gstin']=''
                self.send({'ok':True,'consent':s['consent']}); return
            if path=='/api/upload':
                if not s['consent']: raise ValueError('KYC consent is required')
                kind=body.get('kind')
                if kind not in ('gst','udyam','signatory','address'): raise ValueError('Choose document type')
                try: data=base64.b64decode(body.get('data',''),validate=True)
                except ValueError: raise ValueError('Invalid image data')
                if len(data)>4000000: raise ValueError('Image must be smaller than 4 MB')
                if not (data.startswith(b'\x89PNG\r\n\x1a\n') or data.startswith(b'\xff\xd8\xff')): raise ValueError('Upload a PNG or JPEG image')
                text,method=ocr(data)
                s['docs']=[d for d in s['docs'] if d['kind']!=kind]+[{'kind':kind,'text':text,'source':'Uploaded image','method':method}]
                s.pop('kyc',None);s.pop('order',None)
                self.send({'ok':True,'characters':len(text),'method':method,'kind':kind}); return
            if path=='/api/kyc':
                if not s['consent']: raise ValueError('KYC consent is required')
                gstin=str(body.get('gstin','')).strip().upper();udyam=str(body.get('udyam','')).strip().upper()
                result=validate_kyc(s['docs'],gstin,udyam)
                # Revalidate GST-dependent products with the registration actually checked.
                if 'profile' in s and gstin != s['profile']['gstin']:
                    s['profile']['gstin']=gstin
                    if s.get('quote'): s['quote']=quote(s['profile'],[{'id':p['product_id'],'quantity':p['quantity']} for p in s['quote']['items']])
                s['kyc']=result;s.pop('order',None);self.send(safe_result(result));return
            if path=='/api/checkout':
                q=s.get('quote'); k=s.get('kyc')
                if not q or not q['valid']: raise ValueError('A valid quote is required')
                if not s['consent'] or not k or not k['ok']: raise ValueError('Resolve KYC checks before creating an order')
                if body.get('accept_quote') is not True: raise ValueError('Confirm the quote and contract')
                if not q['within_budget'] and body.get('accept_over_budget') is not True: raise ValueError('Confirm the amount above your budget')
                if s.get('order'): self.send({'order':s['order']});return
                eta=TODAY+datetime.timedelta(days=q['install_days'])
                s['order']={'id':'UD-'+secrets.token_hex(3).upper(),'stage':0,'monthly':q['monthly'],'setup':q['setup'],'contract':q['contract'],
                            'eta':str(eta),'created':str(TODAY),'simulation':True,
                            'stages':['Order received','Feasibility confirmed','Installation scheduled','Services activated'],
                            'events':[{'stage':'Order received','at':str(TODAY)}]}
                s['docs']=[];s.pop('kyc',None);s['profile']['gstin']='' # clear documents and identifiers after checkout
                self.send({'order':s['order']});return
            if path=='/api/advance':
                order=s.get('order')
                if not order: raise ValueError('Create a demo order first')
                order['stage']=min(3,order['stage']+1);order['events'].append({'stage':order['stages'][order['stage']],'at':'Demo event'})
                self.send({'order':order});return
            self.send({'error':'Not found'},404)
        except AIError as e: self.send({'error':str(e),'fallback':'guided'},503)
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as e: self.send({'error':str(e)},400)
        except subprocess.TimeoutExpired: self.send({'error':'OCR timed out. Try a clearer image.'},400)
        except Exception: self.send({'error':'Could not complete this request. Try again.'},500)

def expire_sessions():
    while True:
        time.sleep(1)
        now=time.time()
        for sid in list(SESSIONS):
            session=SESSIONS.get(sid)
            if session and now-session['seen']>1800: SESSIONS.pop(sid,None)

if __name__=='__main__':
    threading.Thread(target=expire_sessions,daemon=True).start()
    port=int(os.environ.get('PORT',8765))
    try: server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    except OSError as e:
        if e.errno in (48,98):
            raise SystemExit(f'Port {port} is already in use. Stop the old Udyam server with Control-C in its terminal, then run python3 server.py again. To use a separate port: PORT=8766 python3 server.py')
        raise
    mode='AI configured' if ai_status()['configured'] else 'guided mode; AI key not configured'
    print(f'Udyam Digital: http://127.0.0.1:{port} ({mode})',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()

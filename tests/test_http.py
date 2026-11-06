"""End-to-end HTTP tests: consent, state isolation and checkout gates."""
import unittest,sys,json,threading,http.cookiejar,urllib.request,urllib.error,base64
from pathlib import Path
from unittest.mock import patch
from test_ai import response,COMPLETE
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import Handler,ThreadingHTTPServer
class HTTPFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
    def setUp(self):
        self.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.csrf=self.req('bootstrap')[1]['csrf']
    def req(self,path,body=None,headers=None):
        request=urllib.request.Request(self.base+'/api/'+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json','X-CSRF-Token':getattr(self,'csrf',''),**(headers or {})})
        try:
            with self.client.open(request) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as e:
            with e:return e.code,json.load(e)
    def recommend(self):return self.req('recommend',{'segment':'prof','employees':5,'sites':1,'tier':2,'budget':5000,'term':12,'fibre':True,'needs':['internet','email','security']})
    def verified(self):
        self.recommend();self.req('consent',{'consent':True});_,sample=self.req('specimen/K12');return self.req('kyc',{'gstin':sample['gstin'],'udyam':sample['udyam']})
    def test_locale_resource_is_valid_json(self):
        with self.client.open(self.base+'/locales.json') as r:
            self.assertEqual(r.status,200)
            data=json.load(r)
        self.assertEqual(set(data),{'hi','bn','as','ta','te','mr','gu','kn','ml','pa','or'})
        self.assertIn('sites',data['as']['questions'])
    def test_existing_tools_comparison_survives_quote_edits(self):
        status,data=self.req('recommend',{'segment':'prof','employees':5,'sites':1,'tier':2,'budget':3000,'term':12,'fibre':True,'needs':['internet','email'],'current_tools':['broadband','personal_email']})
        self.assertEqual(status,200)
        self.assertEqual(data['quote']['monthly'],2124)
        self.assertEqual([row['reason'] for row in data['quote']['setup_comparison']],['internet','email'])
        status,data=self.req('quote',{'items':[{'id':'P02','quantity':1}]})
        self.assertEqual(status,200)
        self.assertEqual(data['setup_comparison'][1]['reason'],'unchanged')
        self.assertEqual(data['setup_comparison'][1]['products'],[])
    def test_consent_before_specimen(self):self.assertEqual(self.req('specimen/K12')[0],400)
    def test_consent_before_upload(self):self.assertEqual(self.req('upload',{'kind':'gst','data':''})[0],400)
    def test_csrf_blocks_mutation(self):self.assertEqual(self.req('consent',{'consent':True},{'X-CSRF-Token':'wrong'})[0],403)
    def test_origin_blocks_mutation(self):self.assertEqual(self.req('consent',{'consent':True},{'Origin':'https://untrusted.example'})[0],403)
    def test_checkout_requires_kyc(self):
        self.recommend();self.assertEqual(self.req('checkout',{'accept_quote':True})[0],400)
    def test_checkout_requires_confirmation(self):
        self.assertTrue(self.verified()[1]['ok']);self.assertEqual(self.req('checkout',{})[0],400)
    def test_happy_flow_and_tracker(self):
        self.assertTrue(self.verified()[1]['ok']);status,r=self.req('checkout',{'accept_quote':True});self.assertEqual(status,200)
        self.assertEqual(r['order']['monthly'],2619);self.assertEqual(r['order']['eta'],'2026-07-20')
        self.assertEqual(self.req('advance',{})[1]['order']['stage'],1)
    def test_withdrawal_revokes_verification(self):
        self.verified();self.req('consent',{'consent':False});self.assertEqual(self.req('checkout',{'accept_quote':True})[0],400)
    def test_bad_image(self):
        self.req('consent',{'consent':True});self.assertEqual(self.req('upload',{'kind':'gst','data':base64.b64encode(b'not an image').decode()})[0],400)
    def test_static_cannot_expose_dataset(self):
        with self.assertRaises(urllib.error.HTTPError):self.client.open(self.base+'/data/mock_gstin_registry.csv')
    def test_second_session_cannot_read_order(self):
        self.verified();self.req('checkout',{'accept_quote':True})
        other=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.assertIsNone(json.load(other.open(self.base+'/api/order'))['order'])
    def test_ai_requires_separate_consent(self):
        self.assertEqual(self.req('ai/chat',{'message':'Hello'})[0],400)
    def test_ai_missing_key_is_clear(self):
        self.req('ai/consent',{'consent':True})
        with patch('server.ai_status',return_value={'configured':False}):
            status,result=self.req('ai/chat',{'message':'Hello'})
        self.assertEqual(status,503);self.assertEqual(result['fallback'],'guided')
    def test_ai_quote_enters_existing_checkout_flow(self):
        self.req('ai/consent',{'consent':True})
        with patch('server.ai_status',return_value={'configured':True}),patch('ai_advisor.call_model',return_value=response(**COMPLETE)):
            status,result=self.req('ai/chat',{'message':'A clinic with internet and email'})
        self.assertEqual(status,200);self.assertEqual(result['quote']['monthly'],2124)
        self.assertEqual(self.req('checkout',{'accept_quote':True})[0],400)
    def test_ai_withdrawal_clears_history(self):
        self.req('ai/consent',{'consent':True});self.req('ai/consent',{'consent':False})
        self.assertEqual(self.req('ai/chat',{'message':'Hello'})[0],400)
    def test_recheck_mismatch_blocks_checkout(self):
        self.verified();self.req('kyc',{'gstin':'INVALID','udyam':''});self.assertEqual(self.req('checkout',{'accept_quote':True})[0],400)
if __name__=='__main__':unittest.main()

import sys,unittest,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import *
class Rules(unittest.TestCase):
    def b(self,**kw): return profile({'segment':'prof','employees':5,'sites':1,'tier':2,'budget':5000,'term':12,'fibre':True,'needs':['internet','email','security'],**kw})
    def test_clinic_quote(self):
        r=recommend(self.b());self.assertEqual(r['quote']['monthly'],2619);self.assertTrue(r['quote']['valid'])
    def test_current_tools_do_not_change_prices_or_add_products(self):
        baseline=recommend(self.b())['quote']
        actual=recommend(self.b(current_tools=['personal_email','broadband']))['quote']
        self.assertEqual(actual['monthly'],baseline['monthly'])
        self.assertEqual([p['product_id'] for p in actual['items']],[p['product_id'] for p in baseline['items']])
        self.assertEqual([row['reason'] for row in actual['setup_comparison']],['email','internet'])
    def test_comparison_updates_when_product_removed(self):
        b=self.b(current_tools=['personal_email','broadband'])
        q=quote(b,[{'id':'P02','quantity':1}])
        self.assertEqual(q['setup_comparison'][0],{'tool':'personal_email','reason':'unchanged','products':[]})
        self.assertEqual(q['setup_comparison'][1]['products'],['Biz Fibre 300'])
    def test_none_and_skip_are_explicit_and_distinct(self):
        self.assertEqual(recommend(self.b(current_tools=['none']))['quote']['setup_comparison'][0]['reason'],'new')
        self.assertEqual(recommend(self.b(current_tools=['skip']))['quote']['setup_comparison'][0]['reason'],'unknown')
        with self.assertRaises(ValueError):self.b(current_tools=['none','billing'])
    def test_firewall_is_not_described_as_device_antivirus(self):
        b=self.b(current_tools=['security'])
        q=quote(b,[{'id':'P02','quantity':1},{'id':'P21','quantity':1}])
        self.assertEqual(q['setup_comparison'][0]['reason'],'unchanged')
        self.assertEqual(q['setup_comparison'][0]['products'],[])
    def test_registry_checksum(self):
        self.assertTrue(all(gst_checksum(x) for x in GST));self.assertTrue(lookup_gst(next(k for k,v in GST.items() if v['status']=='Active'))['ok'])
    def test_altered_checksum(self):
        x=next(iter(GST));self.assertFalse(lookup_gst(x[:-1]+('0' if x[-1]!='0' else '1'))['ok'])
    def test_inactive_registry(self):
        key=next(k for k,v in GST.items() if v['status']!='Active');self.assertFalse(lookup_gst(key)['ok'])
    def test_unknown_registry(self):
        self.assertFalse(lookup_gst('INVALID')['ok'])
    def test_gst_required(self):
        q=quote(self.b(),[{'id':'P15','quantity':1}]);self.assertFalse(q['valid'])
    def test_no_fibre_uses_wireless(self):
        q=recommend(self.b(fibre=False))['quote'];self.assertIn('P04',[x['product_id'] for x in q['items']]);self.assertTrue(q['valid'])
    def test_fibre_dependency_rejected(self):
        q=quote(self.b(fibre=False),[{'id':'P04','quantity':1},{'id':'P09','quantity':1}]);self.assertFalse(q['valid'])
    def test_contract_respected(self):
        r=recommend(self.b(term=1));self.assertIsNone(r['quote'])
    def test_budget_is_honest(self):
        r=recommend(self.b(budget=100))['quote'];self.assertFalse(r['within_budget']);self.assertEqual(len(r['items']),3)
    def test_site_quantity(self):
        q=quote(self.b(sites=3),[{'id':'P01','quantity':1}]);self.assertFalse(q['valid'])
    def test_min_sites(self):
        q=quote(self.b(),[{'id':'P10','quantity':1},{'id':'P01','quantity':1}]);self.assertFalse(q['valid'])
    def test_duplicate_products(self):
        with self.assertRaises(ValueError):quote(self.b(),[{'id':'P01','quantity':1}]*2)
    def test_fractional_quantity(self):
        with self.assertRaises(ValueError):quote(self.b(),[{'id':'P01','quantity':1.5}])
    def test_tier_restriction(self):
        self.assertIn('Unavailable in this city tier',eligible(PRODUCTS['P03'],self.b()))
    def test_missing_docs_fail_closed(self):
        self.assertFalse(validate_kyc([])['ok'])
    def test_expired_id(self):
        r=validate_kyc([{'kind':'signatory','text':'Designation Owner\nValid till 2020-01-01\nFor business Example'}]);
        self.assertTrue(any(c['title']=='Signatory ID validity' and not c['ok'] for c in r['checks']))
    def test_old_bill(self):
        r=validate_kyc([{'kind':'address','text':'Bill date 2026-01-01\nSupply address Example'}]);
        self.assertTrue(any(c['title']=='Address proof age' and not c['ok'] for c in r['checks']))
    def test_future_bill(self):
        r=validate_kyc([{'kind':'address','text':'Bill date 2026-08-01\nSupply address Example'}]);
        self.assertTrue(any(c['title']=='Address proof age' and not c['ok'] for c in r['checks']))
    def test_employee_authority_needs_review(self):
        r=validate_kyc([{'kind':'signatory','text':'Designation Office admin\nValid till 2028-01-01'}]);
        self.assertTrue(any(c['title']=='Signatory authority' and not c['ok'] for c in r['checks']))
if __name__=='__main__':unittest.main()

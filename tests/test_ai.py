"""GenAI contract tests use mocked provider responses, never a paid API call."""
import copy,io,json,os,sys,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ai_advisor as ai

def response(**updates):return {'reply':'Thanks. Let’s find a suitable bundle.','clarification':None,'profile':{k:updates.get(k) for k in ai.FIELDS}}
COMPLETE={'current_tools':['broadband','personal_email'],'business_type':'Clinic','segment':'prof','employees':5,'sites':1,'tier':2,'budget':3000,'term':12,'fibre':True,'needs':['internet','email']}
class Advisor(unittest.TestCase):
 def setUp(self):
  self.provider_patch=patch.dict(os.environ,{'AI_PROVIDER':'openai'});self.provider_patch.start()
 def tearDown(self):self.provider_patch.stop()
 def turn(self,data,state=None,message='I run a clinic',language='en'):
  with patch.object(ai,'call_model',return_value=data):return ai.chat_turn(state or {},message,language)
 def test_missing_fields_are_not_defaulted(self):
  r,s=self.turn(response(business_type='Clinic',segment='prof'))
  self.assertIsNone(r['quote']);self.assertIn('sites',r['missing']);self.assertNotIn('sites',s['known'])
 def test_complete_profile_uses_authoritative_price(self):
  r,s=self.turn(response(**COMPLETE));self.assertEqual(r['quote']['monthly'],2124);self.assertTrue(r['quote']['valid'])
 def test_budget_correction_reprices(self):
  _,s=self.turn(response(**COMPLETE));r,_=self.turn(response(budget=1000),s,'My budget is only 1000')
  self.assertFalse(r['quote']['within_budget']);self.assertEqual(r['profile']['budget'],1000)
 def test_no_fibre_routes_to_wireless(self):
  r,_=self.turn(response(**{**COMPLETE,'fibre':False}));self.assertEqual(r['quote']['items'][0]['product_id'],'P04')
 def test_short_term_does_not_invent_eligibility(self):
  r,_=self.turn(response(**{**COMPLETE,'term':1}));self.assertIsNone(r['quote'])
 def test_ambiguous_backup_asks_before_quote(self):
  data=response(**COMPLETE);data['clarification']='backup_kind';data['profile']['needs']=['internet','email','backup']
  r,state=self.turn(data,message='बैकअप भी जोड़ें',language='hi')
  self.assertIsNone(r['quote']);self.assertEqual(r['missing'],['backup_kind']);self.assertIn('या दोनों',r['reply'])
 def test_ambiguity_preserves_existing_needs(self):
  _,state=self.turn(response(**COMPLETE));data=response(needs=['backup']);data['clarification']='backup_kind'
  r,newstate=self.turn(data,state,'Add backup')
  self.assertEqual(newstate['known']['needs'],['internet','email']);self.assertIsNone(r['quote'])
 def test_both_backup_types_are_distinct_products(self):
  r,_=self.turn(response(**{**COMPLETE,'needs':['internet','email','backup','failover']}))
  ids={p['product_id'] for p in r['quote']['items']};self.assertTrue({'P17','P09'}<=ids)
 def test_network_failover_does_not_include_cloud_backup(self):
  r,_=self.turn(response(**{**COMPLETE,'needs':['internet','email','failover']}),message='इंटरनेट बैकअप जोड़ें',language='hi')
  ids={p['product_id'] for p in r['quote']['items']};self.assertIn('P09',ids);self.assertNotIn('P17',ids)
 def test_missing_hindi_question(self):
  r,_=self.turn(response(),language='hi');self.assertIn('आप किस प्रकार',r['reply'])
 def test_invalid_model_field_rejected(self):
  with self.assertRaises(ai.AIError):self.turn(response(employees=-10))
 def test_boolean_is_not_employee_number(self):
  with self.assertRaises(ai.AIError):self.turn(response(employees=True))
 def test_unknown_service_rejected(self):
  with self.assertRaises(ai.AIError):self.turn(response(needs=['P99']))
 def test_malformed_structure_rejected(self):
  with self.assertRaises(ai.AIError):self.turn({'reply':'hello','profile':{'budget':1000}})
 def test_numeric_price_claim_not_displayed(self):
  d=response();d['reply']='Your plan costs ₹1 forever';r,_=self.turn(d);self.assertNotIn('₹',r['reply']);self.assertNotIn('forever',r['reply'])
 def test_clinic_reply_is_one_english_question_even_if_model_switches_language(self):
  d=response(business_type='Clinic',segment='prof',employees=5,budget=3000)
  d['reply']='नमस्ते। क्या इंटरनेट या सीसीटीवी चाहिए? We promise free installation!'
  r,state=self.turn(d,message='3000/month. five employees in clinic')
  self.assertEqual(r['reply'],'How many business locations do you have?')
  self.assertEqual(state['known']['budget'],3000)
  self.assertEqual(state['known']['employees'],5)
  self.assertIsNone(r['quote'])
  r,state=self.turn(response(sites=1),state,'1')
  self.assertEqual(r['reply'],ai.QUESTIONS['en']['current_tools'])
  r,state=self.turn(response(current_tools=['broadband','personal_email']),state,'We use broadband and Gmail')
  self.assertEqual(r['reply'],ai.QUESTIONS['en']['needs'])
  self.assertNotIn('tier',state['known'])
  self.assertEqual(state['known']['employees'],5)
 def test_hindi_reply_ignores_english_or_multiple_model_questions(self):
  d=response(business_type='Clinic',segment='prof',employees=5,budget=3000)
  d['reply']='Which services? Where are you based?'
  r,_=self.turn(d,language='hi')
  self.assertEqual(r['reply'],ai.QUESTIONS['hi']['sites'])
 def test_language_switch_and_known_fields_are_respected(self):
  state={'known':{'business_type':'Clinic','segment':'prof','employees':5,'sites':1,'budget':3000},'history':[]}
  r,_=self.turn(response(),state,'कृपया आगे बढ़ें',language='hi')
  self.assertEqual(r['reply'],ai.QUESTIONS['hi']['current_tools'])
 def test_known_needs_not_asked_again(self):
  state={'known':{k:v for k,v in COMPLETE.items() if k!='tier'},'history':[]}
  d=response();d['reply']='Do you need internet or CCTV?'
  r,_=self.turn(d,state,'Continue')
  self.assertEqual(r['reply'],ai.QUESTIONS['en']['tier'])
 def test_pending_question_is_sent_for_short_answer_extraction(self):
  known={'business_type':'Clinic','segment':'prof','employees':5,'budget':3000}
  provider={'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(response(sites=1))}]}]}
  with patch.dict(os.environ,{'OPENAI_API_KEY':'sk-fake-test-key'}),patch.object(ai.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(provider).encode())) as send:
   ai.call_model([{'role':'user','content':'1'}],known,'en')
   instructions=json.loads(send.call_args.args[0].data)['instructions']
   context=json.loads(instructions.split('Trusted application context:\n')[1])
   self.assertEqual(context['pending_field'],'sites')
   self.assertEqual(context['pending_question'],ai.QUESTIONS['en']['sites'])
 def test_regional_languages_control_every_advisor_stage(self):
  for code,locale in ai.LOCALES.items():
   with self.subTest(language=code):
    r,state=self.turn(response(business_type='Clinic',segment='prof',employees=5,budget=3000),language=code)
    self.assertEqual(r['reply'],locale['questions']['sites'])
    r,state=self.turn(response(sites=1),state,'1',language=code)
    self.assertEqual(r['reply'],locale['questions']['current_tools'])
    r,state=self.turn(response(current_tools=['skip']),state,'Not sure',language=code)
    self.assertEqual(r['reply'],locale['questions']['needs'])
    r,_=self.turn(response(**COMPLETE),language=code)
    self.assertEqual(r['reply'],locale['copy']['ready'])
    self.assertEqual(r['profile']['language'],code)
    r,_=self.turn(response(**{**COMPLETE,'budget':1000}),language=code)
    self.assertEqual(r['reply'],locale['copy']['over_budget'].format(over=f"{r['quote']['over_budget']:,}"))
    data=response(**COMPLETE);data['clarification']='backup_kind'
    r,_=self.turn(data,language=code)
    self.assertEqual(r['reply'],locale['copy']['backup_kind'])
    self.assertIsNone(r['quote'])
 def test_regional_copy_resources_are_complete(self):
  for code,locale in ai.LOCALES.items():
   self.assertEqual(set(locale['questions']),set(ai.REQUIRED))
   self.assertTrue(all(locale['questions'].values()))
   for key in ('disclosure','consent'):
    self.assertIn('{provider}',locale['copy'][key])
   self.assertIn('{over}',locale['copy']['over_budget'])
 def test_all_locales_have_the_same_ui_coverage(self):
  expected=set(ai.LOCALES['mr']['ui'])
  self.assertGreaterEqual(len(expected),300)
  for code,locale in ai.LOCALES.items():
   self.assertEqual(set(locale['ui']),expected,code)
 def test_ui_translations_preserve_placeholders_and_numbers(self):
  import re,unicodedata
  def numbers(value):
   return re.findall(r'\d+',''.join(str(unicodedata.digit(c)) if c.isdigit() else c for c in value))
  for code,locale in ai.LOCALES.items():
   for source,target in locale['ui'].items():
    self.assertEqual(sorted(re.findall(r'\{\w+\}',source)),sorted(re.findall(r'\{\w+\}',target)),(code,source))
    self.assertEqual(numbers(source),numbers(target),(code,source))
    self.assertNotIn('<',re.sub(r'<br\s*/?>','',target),(code,source))
 def test_current_tools_are_required_before_quote(self):
  data=response(**{k:v for k,v in COMPLETE.items() if k!='current_tools'})
  r,state=self.turn(data)
  self.assertIsNone(r['quote'])
  self.assertEqual(r['reply'],ai.QUESTIONS['en']['current_tools'])
  r,state=self.turn(response(current_tools=['skip']),state,'Prefer not to say')
  self.assertIsNotNone(r['quote'])
 def test_invalid_existing_tools_fail_closed(self):
  for value in ('gmail',['secret_tool'],['none','personal_email'],['skip','broadband']):
   with self.subTest(value=value),self.assertRaises(ai.AIError):self.turn(response(current_tools=value))
 def test_existing_tools_are_not_requested_services(self):
  r,state=self.turn(response(business_type='Clinic',segment='prof',employees=5,sites=1,current_tools=['personal_email','broadband']))
  self.assertNotIn('needs',state['known'])
  self.assertEqual(r['reply'],ai.QUESTIONS['en']['needs'])
 def test_current_tools_correction_preserves_other_profile_details(self):
  _,state=self.turn(response(**COMPLETE))
  r,state=self.turn(response(current_tools=['business_email']),state,'Actually we already have business email')
  self.assertEqual(state['known']['needs'],COMPLETE['needs'])
  self.assertEqual(r['quote']['monthly'],2124)
  self.assertEqual(r['quote']['setup_comparison'][0]['reason'],'existing_email')
 def test_privacy_redaction(self):
  text=ai.redact('sk-proj-abc123456789012345 37NBLXS1145E1ZU UDYAM-AP-00-5186772 me@example.com 9876543210')
  for value in ('sk-proj','37NBLXS','UDYAM-AP','me@example.com','9876543210'):self.assertNotIn(value,text)
 def test_original_state_unchanged_on_error(self):
  state={'known':{'budget':5000},'history':[]};original=copy.deepcopy(state)
  with patch.object(ai,'call_model',side_effect=ai.AIError('offline')):
   with self.assertRaises(ai.AIError):ai.chat_turn(state,'Hello')
  self.assertEqual(state,original)
 def test_incomplete_provider_response_rejected(self):
  with self.assertRaises(ai.AIError):ai.output_json({'status':'incomplete','output':[]})
 def test_refusal_handled(self):
  with self.assertRaises(ai.AIError):ai.output_json({'status':'completed','output':[{'content':[{'type':'refusal','refusal':'no'}]}]})
 def test_call_uses_fixed_endpoint_and_no_store(self):
  provider={'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(response())}]}]}
  with patch.dict(os.environ,{'OPENAI_API_KEY':'sk-test-not-a-real-key','OPENAI_MODEL':'gpt-5.4-mini'}),patch.object(ai.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(provider).encode())) as send:
   ai.call_model([{'role':'user','content':'My GSTIN is 37NBLXS1145E1ZU'}],{},'en')
   request=send.call_args.args[0];payload=json.loads(request.data)
   self.assertEqual(request.full_url,'https://api.openai.com/v1/responses');self.assertFalse(payload['store'])
   self.assertNotIn('37NBLXS1145E1ZU',request.data.decode());self.assertTrue(payload['text']['format']['strict'])
 def test_missing_key_no_network(self):
  with patch.dict(os.environ,{'OPENAI_API_KEY':''}),patch.object(ai.urllib.request,'urlopen') as send:
   with self.assertRaises(ai.AIError):ai.call_model([],{},'en')
   send.assert_not_called()
 def test_quota_error_distinct_from_rate_limit(self):
  for code,expected in [('insufficient_quota','billing quota'),('credit_balance_exhausted','billing quota'),('rate_limit_exceeded','Temporary API rate limit'),('project_spend_limit_exceeded','billing/usage limit')]:
   error=urllib.error.HTTPError('https://api.openai.com/v1/responses',429,'blocked',{},io.BytesIO(json.dumps({'error':{'code':code,'message':'private account info'}}).encode()))
   with patch.dict(os.environ,{'OPENAI_API_KEY':'sk-fake-test-key'}),patch.object(ai.urllib.request,'urlopen',side_effect=error):
    with self.assertRaises(ai.AIError) as caught:ai.call_model([],{},'en')
    self.assertIn(expected,str(caught.exception));self.assertNotIn('private account',str(caught.exception))
 def test_provider_error_is_sanitized(self):
  error=urllib.error.HTTPError('https://api.openai.com/v1/responses',401,'bad',{},io.BytesIO(b'secret-sensitive-error'))
  with patch.dict(os.environ,{'OPENAI_API_KEY':'sk-test-not-a-real-key'}),patch.object(ai.urllib.request,'urlopen',side_effect=error):
   with self.assertRaises(ai.AIError) as caught:ai.call_model([],{},'en')
   self.assertNotIn('secret-sensitive',str(caught.exception))

class Gemini(unittest.TestCase):
 def setUp(self):
  self.env=patch.dict(os.environ,{'AI_PROVIDER':'gemini','GEMINI_API_KEY':'AIza-fake-test-key-not-real','GEMINI_MODEL':'gemini-3.1-flash-lite','OPENAI_API_KEY':'sk-never-send-this-key'});self.env.start()
 def tearDown(self):self.env.stop()
 def test_gemini_endpoint_and_key_are_isolated(self):
  provider={'choices':[{'finish_reason':'stop','message':{'content':json.dumps(response(**COMPLETE))}}]}
  with patch.object(ai.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(provider).encode())) as send:
   data=ai.call_model([{'role':'user','content':'Clinic'}],{},'en')
   req=send.call_args.args[0];payload=json.loads(req.data)
   self.assertEqual(req.full_url,'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions')
   self.assertEqual(req.get_header('Authorization'),'Bearer AIza-fake-test-key-not-real')
   self.assertNotIn('sk-never-send',str(req.headers));self.assertEqual(payload['model'],'gemini-3.1-flash-lite')
   self.assertEqual(data['profile']['employees'],5)
   self.assertEqual(payload['reasoning_effort'],'low')
 def test_gemini_no_key_does_not_fallback_to_openai(self):
  with patch.dict(os.environ,{'GEMINI_API_KEY':''}),patch.object(ai.urllib.request,'urlopen') as send:
   with self.assertRaises(ai.AIError):ai.call_model([],{},'en')
   send.assert_not_called()
 def test_gemini_quota_is_clear_and_has_no_fallback(self):
  error=urllib.error.HTTPError('https://generativelanguage.googleapis.com',429,'quota',{},io.BytesIO(b'{"error":{"status":"RESOURCE_EXHAUSTED"}}'))
  with patch.object(ai.urllib.request,'urlopen',side_effect=error) as send:
   with self.assertRaises(ai.AIError) as caught:ai.call_model([],{},'en')
   self.assertIn('Gemini free-tier quota',str(caught.exception));self.assertEqual(send.call_count,1)
 def test_gemini_truncated_response_fails_closed(self):
  data={'choices':[{'finish_reason':'length','message':{'content':'{}'}}]}
  with patch.object(ai.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(data).encode())):
   with self.assertRaises(ai.AIError):ai.call_model([],{},'en')
 def test_gemini_key_redaction(self):
  self.assertNotIn('AIza',ai.redact('oops AIza-fake-test-key-not-real'))
 def test_unknown_provider_disabled(self):
  with patch.dict(os.environ,{'AI_PROVIDER':'unknown'}):self.assertFalse(ai.ai_status()['configured'])

if __name__=='__main__':unittest.main()

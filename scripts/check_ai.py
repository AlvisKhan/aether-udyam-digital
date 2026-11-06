#!/usr/bin/env python3
"""One real API smoke test with a fictional business. Usage may incur a charge."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from config import ai_status
from ai_advisor import chat_turn,AIError
if not ai_status()['configured']:sys.exit('No key configured. Run python3 scripts/setup_ai.py first.')
print('Sending one synthetic business message to '+ai_status()['provider']+'. Your account quota/billing rules apply.')
message='I run a clinic with five employees at one tier-2 city location. Fibre is available. I need internet and business email for all five employees. My budget is 3000 rupees a month before taxes and my maximum contract is twelve months.'
try:
 result,_=chat_turn({},message)
 if result['missing']:sys.exit('Connected, but extraction needs clarification: '+', '.join(result['missing'])+'. Test the chat before recording the demo.')
 if not result['quote'] or not result['quote']['valid']:sys.exit('Connected, but the returned requirements did not produce a valid quote. Review the chat.')
 print('Connected to '+ai_status()['provider']+'. Model: '+ai_status()['model'])
 print('Server-calculated monthly quote: INR '+str(result['quote']['monthly']))
 if result['quote']['monthly']!=2124:sys.exit('Price differs from the expected INR 2124 scenario. Review extracted requirements before the demo.')
 print('Smoke test passed. Restart the app server if you configured the key after it started.')
except (AIError,ValueError) as e:sys.exit(str(e))

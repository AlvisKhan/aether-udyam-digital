#!/usr/bin/env python3
"""Hidden local key setup. Gemini by default; no network calls or key logging."""
import argparse,getpass,os,re,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Configure an AI provider privately. Defaults to Gemini.')
parser.add_argument('--provider',choices=['gemini','openai'],default='gemini')
args=parser.parse_args()
provider=args.provider; label='Gemini' if provider=='gemini' else 'OpenAI'
default='gemini-3.1-flash-lite' if provider=='gemini' else 'gpt-5.4-mini'
print('Aether Udyam · local '+label+' setup')
print('Paste your API key at the hidden prompt. It will be stored only in the ignored .env file.')
if provider=='gemini':print('Use a Google AI Studio free-tier project. Free quotas depend on your account; this script does not enable billing.')
if not sys.stdin.isatty():sys.exit('Run this directly in Terminal so the key can be entered privately.')
key=getpass.getpass(label+' API key (hidden): ').strip()
valid=bool(re.fullmatch(r'[A-Za-z0-9._\-]{20,512}',key)) if provider=='gemini' else bool(re.fullmatch(r'sk-[A-Za-z0-9_\-]{15,}',key))
if not valid:sys.exit('The key format was not recognised. No changes were made.')
print('Next: press Enter to use '+default+'. This is a model prompt, not a shell command.')
while True:
    model=input('Model [press Enter for '+default+']: ').strip() or default
    if re.fullmatch(r'[a-zA-Z0-9._\-]+',model):break
    print('Enter only a model name, or press Enter. Your key is held privately; no need to re-enter it.')
# Preserve the other provider, but select only the chosen one. Never auto-fallback to a paid provider.
allowed={'AI_PROVIDER','GEMINI_API_KEY','GEMINI_MODEL','OPENAI_API_KEY','OPENAI_MODEL'}
values={}
if (root/'.env').exists():
    for line in (root/'.env').read_text().splitlines():
        name,sep,value=line.partition('=')
        if sep and name.strip() in allowed:values[name.strip()]=value.strip()
values.update({'AI_PROVIDER':provider,provider.upper()+'_API_KEY':key,provider.upper()+'_MODEL':model})
fd,tmp=tempfile.mkstemp(prefix='.env-',dir=root)
try:
    os.fchmod(fd,0o600)
    with os.fdopen(fd,'w') as f:f.write(''.join(name+'='+value+'\n' for name,value in values.items()))
    os.replace(tmp,root/'.env')
finally:
    if os.path.exists(tmp):os.unlink(tmp)
print('Saved locally. Provider: '+label+'. Key not displayed.')
print('At the normal terminal prompt, run: python3 scripts/check_ai.py')
print('Then restart the app server. No API request was made by setup.')

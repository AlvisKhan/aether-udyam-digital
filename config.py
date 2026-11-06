"""Read a small allowlist from a local ignored .env without printing credentials."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ALLOWED={'AI_PROVIDER','GEMINI_API_KEY','GEMINI_MODEL','OPENAI_API_KEY','OPENAI_MODEL'}
def load_env():
    path=ROOT/'.env'
    if not path.exists():return
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):continue
        key,sep,value=line.partition('=')
        if sep and key.strip() in ALLOWED:
            value=value.strip()
            if len(value)>=2 and value[0]==value[-1] and value[0] in ('\"',"'"):value=value[1:-1]
            os.environ.setdefault(key.strip(),value)
def ai_status():
    provider=os.environ.get('AI_PROVIDER','').strip().lower() or ('gemini' if os.environ.get('GEMINI_API_KEY','').strip() else 'openai')
    if provider=='gemini':
        return {'configured':bool(os.environ.get('GEMINI_API_KEY','').strip()),'model':os.environ.get('GEMINI_MODEL','gemini-3.1-flash-lite'),'provider':'Gemini'}
    if provider=='openai':
        return {'configured':bool(os.environ.get('OPENAI_API_KEY','').strip()),'model':os.environ.get('OPENAI_MODEL','gpt-5.4-mini'),'provider':'OpenAI'}
    return {'configured':False,'model':'','provider':'Unsupported'}
load_env()

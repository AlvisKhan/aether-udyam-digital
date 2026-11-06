"""Reproduce actual local OCR extractions. Requires Node, Tesseract.js and Pillow."""
from pathlib import Path
import subprocess,hashlib,json,sys,tempfile
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from image_clean import clean
cache={}
with tempfile.TemporaryDirectory(prefix='udyam-ocr-') as tmp:
    for path in sorted((root/'data/kyc_documents').glob('*.png')):
        cleaned=Path(tmp)/'image.png';clean(path,cleaned)
        r=subprocess.run(['node',str(root/'scripts/ocr.cjs'),str(cleaned)],capture_output=True,text=True,check=True)
        cache[hashlib.sha256(path.read_bytes()).hexdigest()]={'file':path.name,'text':r.stdout.strip()}
        print(path.name,flush=True)
(root/'data/ocr_cache.json').write_text(json.dumps(cache,ensure_ascii=False,indent=2))
print(f'Prepared {len(cache)} actual local OCR extractions. No KYC answers or labels generated.')

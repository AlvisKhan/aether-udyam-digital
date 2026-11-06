#!/usr/bin/env python3
"""Download the official English Tesseract model once; OCR then runs locally."""
import hashlib,urllib.request
from pathlib import Path
URL='https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/eng.traineddata'
SHA256='7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2'
def install():
    target=Path(__file__).resolve().parents[1]/'data/eng.traineddata'
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==SHA256:print('Verified English OCR model already available.');return
    print('Downloading official tessdata_fast English model (Apache-2.0); no document data is sent.')
    with urllib.request.urlopen(URL,timeout=60) as r:data=r.read(10_000_001)
    if len(data)>10_000_000 or hashlib.sha256(data).hexdigest()!=SHA256:raise SystemExit('Model verification failed; nothing installed.')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);print('OCR model downloaded and SHA-256 verified.')
if __name__=='__main__':install()

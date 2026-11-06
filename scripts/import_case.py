#!/usr/bin/env python3
"""Import only the organiser's four CSVs and specimen images from a folder or ZIP."""
import argparse,zipfile
from pathlib import Path
CSVS={'product_catalogue.csv','smb_leads.csv','mock_gstin_registry.csv','mock_udyam_registry.csv'}
def import_case(source,destination):
    source=Path(source);destination=Path(destination);files={}
    def accept(name,data):
        path=Path(name)
        if '__MACOSX' in path.parts:return
        target=path.name if path.name in CSVS else 'kyc_documents/'+path.name if 'kyc_documents' in path.parts and path.suffix.lower() in ('.png','.jpg','.jpeg') else None
        if target:
            if target in files and files[target]!=data:raise ValueError('Ambiguous duplicate case file: '+target)
            if len(data)>10_000_000:raise ValueError('Case file exceeds 10 MB: '+target)
            files[target]=data
    if source.is_dir():
        for p in source.rglob('*'):
            if p.is_file() and not p.is_symlink():
                if p.name in CSVS or ('kyc_documents' in p.parts and p.suffix.lower() in ('.png','.jpg','.jpeg')):accept(p.relative_to(source),p.read_bytes())
    elif zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as z:
            for info in z.infolist():
                p=Path(info.filename)
                if p.name in CSVS or ('kyc_documents' in p.parts and p.suffix.lower() in ('.png','.jpg','.jpeg')):
                    if info.file_size>10_000_000:raise ValueError('Case file exceeds size limit')
                    accept(info.filename,z.read(info))
    else:raise ValueError('Choose the extracted case-data folder or its ZIP (not the outer case PDF archive).')
    missing=CSVS-set(files)
    if missing:raise ValueError('Missing case CSV files: '+', '.join(sorted(missing)))
    if not any(n.startswith('kyc_documents/') for n in files):raise ValueError('No KYC specimen images found')
    # All targets are allowlisted basenames, never paths supplied by an archive.
    for name,data in files.items():
        target=destination/name
        if target.exists() and target.read_bytes()!=data:raise ValueError('Existing file differs; move it aside before import: '+name)
    for name,data in files.items():
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return len(files)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source');parser.add_argument('--destination',type=Path,default=Path(__file__).resolve().parents[1]/'data');args=parser.parse_args()
    try:print(f'Imported {import_case(args.source,args.destination)} case files locally. No files were uploaded.')
    except (ValueError,OSError,zipfile.BadZipFile) as e:parser.exit(1,str(e)+'\n')

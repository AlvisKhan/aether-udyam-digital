# Local case data

Import the organiser-provided YTL_TrackA_Udyam_Digital_Data folder or ZIP with `python3 scripts/import_case.py /path/to/data-pack` from the repository root. The public repository intentionally does not redistribute the case CSVs, specimen documents or OCR cache. Judges already have the data pack.

For local OCR, run `python3 scripts/setup_ocr.py` to download and hash-check the official Apache-2.0 English model, then `python3 scripts/prepare_ocr.py` to reproduce extraction cache. None of these generated files should be committed.

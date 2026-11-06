# Udyam Digital · Team Aether, NIT Silchar

Airtel SYNC 2026 Digital Track prototype for the fictional Accel Business case. A small-business owner can describe needs, review a transparent bundle, check documents with consent and track a simulated order.

- Live Gemini advisor with structured requirements and server-owned questions; guided offline alternative.
- English, Hindi, Bengali, Assamese, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi and Odia.
- Existing-tool discovery and quote comparisons, without automatically adding products or cancelling existing services.
- Catalogue eligibility, dependencies, contract terms, quantities, setup fees and explicit budget overruns.
- Local OCR with mocked GSTIN/Udyam registries, masked extracted identifiers and expiring sessions.

## Run locally

Requires Python 3.10+ and Node 18+. Run commands from the cloned repository root.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
npm install --ignore-scripts
```

Import the case-data folder or its data ZIP supplied by the organiser (not the outer archive containing only the brief/template):

```sh
python3 scripts/import_case.py "/path/to/YTL_TrackA_Udyam_Digital_Data"
python3 scripts/analyse.py
python3 scripts/setup_ocr.py
.venv/bin/python scripts/prepare_ocr.py
.venv/bin/python server.py
```

Open **http://127.0.0.1:8765/**. The one-time dependency/model setup needs internet; guided recommendations and document OCR then run locally. OCR preparation extracts all specimen images and may take a few minutes. On Windows, use the virtual environment's `Scripts/python` path instead of `.venv/bin/python`.

The case data is not included in this public repository. Judges can import their organiser-provided pack. The importer copies four CSVs and specimen images only; it never extracts arbitrary archive paths or uploads data.

### Optional live AI

```sh
python3 scripts/setup_ai.py
python3 scripts/check_ai.py
```

Enter your own Gemini key only at the hidden Terminal prompt. Setup stores it in ignored `.env`; restart the app afterward. A key is not needed for guided mode. API quota/billing rules depend on your account; the project does not enable billing or switch providers silently. See [AI setup](docs/genai-setup.md). Never commit an API key or enter one in the advisor chat.

## Judge walkthrough

1. Choose a language. Use the AI advisor or guided questions.
2. Describe a five-person clinic, one tier-2 location, fibre available, a 12-month ceiling, INR 3000/month budget, internet and email needs; state that it already uses home broadband and personal Gmail.
3. Expected example: Biz Fibre 300 + five Cloud Email seats, **INR 2124/month before taxes**, no setup fee. Review the current-setup comparison and edit a line item.
4. Continue to verification and give local-processing consent. Load fictional applicant **K12** and check documents. Other supplied specimens contain deliberate problems.
5. Confirm the demo quote and create an order. Use the labelled simulation control to advance its tracker.

## Verification

```sh
python3 -m unittest discover -s tests -v
node tests/test_localization.cjs
```

After importing the case pack and preparing OCR, 84 Python tests passed in the authoring workspace, plus locale display checks. Automated model tests mock provider responses; live synthetic English/Hindi/Assamese/Punjabi checks are documented separately. Not every language has a full live-model evaluation. [Verification record](docs/verification.md).

## Design and business evidence

- [Architecture and data flows](docs/architecture.md)
- [Privacy and security choices](docs/privacy-security.md)
- [Competitive research with official sources](docs/competitor-research.md)
- [Business case and pilot hypotheses](docs/business-case.md)
- [Synthetic dataset findings](docs/data-findings.md)
- [Demo recording script](docs/demo-script.md)

## Prototype boundaries

Government registries, activation and fulfilment are mocked. There is no production authentication, real identity/e-sign verification, payment or serviceability integration. Do not expose this local development server to the internet. Only consented advisor messages go to the configured AI provider; documents stay in the local OCR flow. Free-tier Gemini content may be used by Google for product improvement. Use fictional details.

Prices are synthetic catalogue minimums with taxes excluded. Pilot targets are proposals, not achieved outcomes. Translation drafts were generated with Gemini and checked for keys, numbers and placeholders; native-speaker review remains outstanding. Product names, identifiers and original document contents stay unchanged; some technical messages and case-analysis material remain English.

## Data and third-party materials

Organiser data is imported locally and excluded from Git. The official OCR model is downloaded separately and verified by SHA-256. See [third-party notices](THIRD_PARTY.md). The repository does not claim to be an official Airtel service.

The final demo video will be added after recording.

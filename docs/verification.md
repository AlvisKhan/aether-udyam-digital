# Verification — offline prototype

Executed 5 November 2026.

- 32 automated checks passed: 20 catalogue/KYC rule tests and 12 HTTP journey/security tests.
- Browser verified: default clinic discovery, ₹2,619 quote, consent screen, supplied K12 documents, registry/OCR checks, demo checkout, order creation and tracker update.
- Browser verified: Hindi switch on the tracker.
- All 47 specimen images were processed through local Tesseract. OCR can still misread damaged/rotated or overprinted text; uncertain fields fail to review. These checks do not claim judges' answer-key accuracy.
- Actual OCR cache was generated from image bytes and keyed by SHA-256; no expected KYC decisions were cached.
- K11 was rejected by rule checks for stale address proof and mismatched/unreadable details; K12 passed the implemented checks.

Not yet verified: live GenAI, real registry/payment/installation integrations, external hosting, final slides, demo video or repository access for judges. No final competition submission has been uploaded.

## GenAI integration update

- 54 automated tests passed after adding the AI integration (18 provider-contract tests and 4 additional HTTP tests, alongside the original 32).
- Tests mock provider responses; no real API requests or charges were made.
- Browser checked the AI entry point, missing-key notice, disabled send button before configuration and guided fallback.
- Real API connectivity, model quality and English/Hindi conversations remain pending local key configuration.

## Live Gemini connection

5 November 2026: removed an unsupported MINIMAL thinking setting. Gemini 3.8 Flash subsequently failed/timed out, so selected the available gemini-3.1-flash-lite model. A real synthetic clinic smoke test passed with the expected INR 2124/month quote. The saved model was updated without changing or displaying the key. All 25 provider-contract tests passed after the fix. Full live Hindi and browser conversation evaluation remains outstanding.

Browser live test: Gemini accepted a five-person clinic request in English and produced the expected INR 2124/month quote (Biz Fibre 300 + five email seats).
Live browser continuation: reducing budget to INR 1800 retained five email seats and selected Biz Fibre 100, yielding INR 1624/month. Hindi request for internet backup initially selected Cloud Backup incorrectly; an explicit clarification corrected this to P09 network failover. Final quote INR 2123/month, INR 1500 setup, INR 3623 first payment, with INR 323 budget overrun displayed. AI-to-editable-quote handoff verified. This semantic ambiguity remains a prompt/evaluation improvement item; no claim that first-pass Hindi intent classification is fully reliable.

## Backup intent improvement

Added explicit file-backup vs network-failover definitions, English/Hindi examples, a structured backup_kind clarification result, and a no-quote gate for ambiguous backup requests. Existing unrelated needs survive clarification. Three live Gemini regressions passed: Hindi internet backup -> P09, Hindi file backup -> P17, ambiguous backup -> clarification with no quote. Full suite: 65 passing tests. Hindi over-budget replies now use the server-calculated amount.

Final browser verification after enabling supported low thinking: the complete Hindi request prompted a backup-kind clarification; answering internet connection, not files, produced P01+P16+P09 at INR 2123/month. The INR 323 overrun was explained in Hindi. No P17 file-backup product was included. Browser evidence: docs/improved-hindi-advisor.jpg. Provider intermittently failed/timeouts during earlier checks; guided fallback remains necessary.

## Advisor conversation guardrails · 5 November 2026

The server now chooses one missing-field question in the selected UI language and never displays provider-generated prose. This prevents mixed-language follow-ups, duplicate questions and unsupported free-text offers. Provider context includes the pending field and question to interpret short answers such as “1”. Gemini still extracts structured requirements; type/range/allowed-service checks cannot guarantee semantic extraction accuracy.

Regression coverage includes the clinic message, a single-location answer, language switching, known needs not being asked again, and ignoring wrong-language or promotional provider text. All 70 automated tests passed, with mocked model calls (no provider quota used by tests).

Live browser replay also passed: “3000/month. five employees in clinic” → asks only number of locations; “1” → asks only required services, both in English. Evidence: advisor-guardrails.png.

## Regional languages · 6 November 2026

Added Bengali (bn), Assamese (as), Tamil (ta) and Telugu (te), alongside English and Hindi. Shared locale resources provide server-owned advisor questions, backup clarification, quote-ready/no-match/over-budget replies, regional AI consent and disclosure, plus main navigation and form/action labels. Some supporting copy, catalogue descriptions, option names and validation results remain English; this is partial interface localisation, not a fully translated product. No native-speaker review has been performed.

Live Assamese clinic input with five staff and a 3000 budget correctly advanced to a single Assamese branch-count question. All four regional advisor headings and controls were checked in the browser; Tamil mobile rendering at 390px showed no horizontal overflow. Existing conversation messages retain their original language when switching; subsequent questions use the new selection. Full suite: 73 tests passed; model regression tests use mocked responses. Evidence: regional-advisor.png.

## Twelve-language expansion · 6 November 2026

Added Marathi, Gujarati, Kannada, Malayalam, Punjabi (Gurmukhi) and Odia, giving twelve languages including English. Expanded all eleven non-English locale resources to the same 301 fixed UI strings plus advisor questions and privacy/quote messages. Coverage includes main journey labels, choices, catalogue descriptions, KYC consent and fixed check messages, and tracker labels. Templates preserve dates and amounts. Product names, identifiers, specimen filenames and original document contents remain unchanged; technical errors, some dynamically composed recommendation notes and case-insights material may remain English. Translations were machine drafted; structural checks do not establish linguistic fluency or legal suitability. Native-speaker review remains outstanding.

Validation: 75 Python tests passed, including all locale schema/placeholder/number checks and regional advisor scenarios; node tests/test_localization.cjs passed for eleven locales. Every selector option rendered its own language. Consent screens in all twelve languages had no horizontal overflow at a 390px viewport. Marathi guided journey -> INR 2619/month quote -> K12 specimen checks -> checkout -> tracker passed. Switching the tracker through all six new regional languages preserved INR 2619. A live Punjabi clinic/five-staff/3000 budget message received a single Punjabi locations question. Prior Assamese live check remains documented above. Not every language has a full live-model conversation evaluation.

Evidence: multilingual-tracker.png and twelve-language-advisor.png. Source ZIP refreshed without API keys. The deck still needs final screenshots and evidence refresh after UI approval.

## Current-tools discovery and comparison · 6 November 2026

Closed the current-tools discovery gap in both guided profile and live AI chat. The structured current_tools field supports broadband, hotspot, personal email, business email, billing, device security, other, explicit none and explicit skip. No answer remains unknown; none/skip cannot be mixed with existing tools. All twelve UI languages include the question, choices and comparison explanations. Existing tools stay separate from future needs, prices and eligibility. Each actual quote carries a deterministic comparison using its current line items. Removing email changes the personal-email row to “not replaced”; it does not continue promising business email. Existing paid email warns about licence overlap; migration and switching are not promised automatically. Device-protection copy is not applied to firewall-only purchases.

84 Python tests passed, alongside JS locale display tests. New tests cover missing/invalid existing tools, opt-out, corrections preserving other requirements, unchanged pricing/product selection, comparison recomputation and HTTP quote edits. Browser guided flow checked broadband+Gmail, exclusive none selection, current-setup comparisons, removing email, Hindi translation and mobile fit. Live English clinic request with all other requirements correctly asked about current tools; broadband+Gmail answer produced the expected P02+P16 quote at INR 2124/month and the correct comparison. Evidence: current-tools-comparison.png and current-tools-ai-quote.png.

Source ZIP updated without credentials. Repository publishing, video and final deck/link refresh remain outstanding.

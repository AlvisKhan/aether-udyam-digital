# Activate Gemini (free-tier path)

The setup utility now defaults to Gemini. Keep your Google AI Studio project on the Free tier; model quotas and availability depend on the account. The app does not enable billing, purchase credits or switch automatically to OpenAI.

1. Copy your key from https://aistudio.google.com/api-keys. Do not paste it into a chat or source code.
2. In your project Terminal, run `python3 scripts/setup_ai.py`.
3. Paste the key at **Gemini API key (hidden)** and press Enter.
4. At **Model [press Enter for gemini-3.1-flash-lite]**, press Enter without typing a command.
5. Wait for **Saved locally. Provider: Gemini.** Then run `python3 scripts/check_ai.py` at the normal terminal prompt. This sends one fictional business message to Gemini and consumes model quota. On a paid project, that project's billing rules apply.
6. Once the check passes, stop the previous server with Control-C, run `python3 server.py` and refresh http://127.0.0.1:8765/. Choose **Talk to the AI advisor** and read/accept the Gemini processing notice.

The key is stored in an ignored `.env` with owner-only permissions. Environment variables set in Terminal take precedence; unset AI_PROVIDER if you previously exported a different provider. Gemini is explicitly selected by setup. The old OpenAI key may remain locally for optional use, but is not used by Gemini or as a fallback.

Google lists gemini-3.1-flash-lite with free input/output on the Free tier, subject to quota. Free-tier content may be used to improve Google products: use only fictional business details. KYC documents and registry records remain local. The provider connection uses Google's documented OpenAI-compatible interface, not OpenAI's service.

Example request:

> I run a clinic with five employees at one tier-2 location. Fibre is available. I need internet and email for all five people. My budget is 3000 rupees per month before taxes, and I accept a twelve-month contract.

Expected server-calculated quote: INR 2124/month. After the smoke test, test a Hindi conversation and a budget correction before recording the final demo.

Live Gemini smoke test passed on 5 November 2026 with gemini-3.1-flash-lite, producing the expected INR 2124 monthly quote. Automated tests mock provider replies and verify that Gemini never sends the OpenAI key or falls back to OpenAI on a quota error.

Optional OpenAI setup remains available with `python3 scripts/setup_ai.py --provider openai`.

References: https://ai.google.dev/gemini-api/docs/openai ; https://ai.google.dev/gemini-api/docs/pricing ; https://ai.google.dev/gemini-api/docs/api-key

---

# Previous OpenAI setup reference

The integration is implemented. A real provider call has not been tested yet because an API key has not been configured.

## Your steps

1. Sign in at https://platform.openai.com/.
2. Select or create the project you want to use for this competition prototype. Open Billing (https://platform.openai.com/settings/organization/billing/overview) and configure API billing if needed. Review the displayed rates and controls before adding funds. No purchase or billing change has been made by the agent.
3. Open https://platform.openai.com/api-keys and create a project API key named `Aether Udyam`. Keep it private; do not paste it into Codex chat, source code, screenshots or the advisor chat.
4. In Terminal, run:

```sh
cd "/Users/alviskhan/Documents/ChatGPT/Airtel/udyam-digital"
python3 scripts/setup_ai.py --provider openai
```

Paste the key at the hidden prompt. Press Enter to accept the configured default `gpt-5.4-mini`, or enter another Responses/Structured-Outputs-compatible model you have access to. The utility saves only `OPENAI_API_KEY` and `OPENAI_MODEL` in the project's ignored `.env` with owner-only permissions. It does not make a network call. If you already export OPENAI_API_KEY in your terminal, that environment value takes precedence over the file.

5. Optionally run the single real smoke test:

```sh
python3 scripts/check_ai.py
```

This sends one fictional business request to OpenAI and may incur a usage charge. Success prints a model name and a server-calculated INR 2124 monthly quote; the key is never printed.

6. Stop the old development server with Control-C in the terminal where it is running, then restart it:

```sh
python3 server.py
```

Open or refresh http://127.0.0.1:8765/. Choose **Talk to the AI advisor**, read the data-processing notice and check the consent box. Type a fictional business request. Respond to follow-up questions, then select **Review my bundle**. Continue through the existing local KYC and demo order flow.

Example:

> I run a clinic with five employees at one tier-2 location. Fibre is available. I need internet and email for all five people. My budget is ₹3,000 per month before taxes, and I can accept a twelve-month contract.

Then test a budget correction and a Hindi conversation. Do not record the final competition demo until these live checks pass.

## What is already implemented

- Server-side OpenAI Responses API connection with a strict JSON schema for requirements.
- English/Hindi conversation, missing-information questions, corrections and a reviewable quote.
- Catalogue and quote engine remain authoritative. Unknown products, invalid values and fabricated numeric price claims are rejected or suppressed.
- API key stays out of browser payloads and responses. No browser-side key entry.
- Separate AI consent, conversation clearing and guided fallback.
- KYC documents and registry records are not passed to the model. Common identifiers in typed text are redacted before transmission; redaction is not a guarantee for arbitrary sensitive free text. Use fictional business data only.
- Timeouts, incomplete responses, refusals, missing keys, quota failures and model-access errors produce a guided-fallback message.
- At most twelve requests per minute per session, one in flight, with a bounded conversation and output. These are local safeguards, not an account-wide spending cap.
- Requests use `store: false`; this does not assert zero provider retention. Review provider data controls before any real-customer use.

## Validation

54 automated tests passed using mocked AI responses; no paid requests were made. The live model's Hindi quality, extraction accuracy, latency and account access still need to be checked with your configured key.

Official references: https://developers.openai.com/api/docs/quickstart ; https://developers.openai.com/api/docs/guides/structured-outputs ; https://developers.openai.com/api/docs/models/gpt-5.4-mini

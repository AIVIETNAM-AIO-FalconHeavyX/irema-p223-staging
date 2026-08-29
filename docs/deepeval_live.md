# Live DeepEval Evaluation

`eval/deepeval_live.py` is a manual, authenticated evaluation of the deployed VF AI chat API. It complements the local retrieval benchmark, Ragas baseline, and Braintrust traces.

## Install

Keep DeepEval out of the application runtime image unless an evaluation image is intentionally being built. The evaluation requirements contain only the API client and DeepEval, not the full OCR/video application stack:

```powershell
pip install -r requirements-eval.txt
```

## Configure runtime credentials

Provide credentials through the shell or a secret manager. The runner keeps passwords and JWTs in memory and never writes them to the report.

```powershell
$env:DEEPEVAL_API_URL = "https://staging.example.com"
$env:OPENAI_API_KEY = "..."
$env:DEEPEVAL_SALES_EMAIL = "..."
$env:DEEPEVAL_SALES_PASSWORD = "..."
$env:DEEPEVAL_TECHNICIAN_EMAIL = "..."
$env:DEEPEVAL_TECHNICIAN_PASSWORD = "..."
$env:DEEPEVAL_ACCOUNTING_EMAIL = "..."
$env:DEEPEVAL_ACCOUNTING_PASSWORD = "..."
$env:DEEPEVAL_GENERAL_EMAIL = "..."
$env:DEEPEVAL_GENERAL_PASSWORD = "..."
```

The API role returned during login must match the dataset role. `sale`/`sales`, `accountant`/`accounting`, and `ktv`/`technician` are normalized aliases; the client cannot spoof a role in the request.

## Run

Start with a small staging probe:

```powershell
python eval/deepeval_live.py --environment staging --limit 2
```

The exact evaluator model is configurable. The default is `gpt-4o-mini`:

```powershell
$env:DEEPEVAL_JUDGE_MODEL = "gpt-5.6-sol"
python eval/deepeval_live.py --environment staging --limit 2
```

The runner validates that exact model identifier with the OpenAI account before logging into the chatbot. `gpt-5.6` is intentionally not treated as a model name because it is ambiguous.

Production requires an explicit acknowledgement:

```powershell
python eval/deepeval_live.py --environment production --allow-production --limit 2
```

## Safety and reports

- Every case uses a fresh persistent conversation ID, so the API will create conversation history and normal Langfuse/Braintrust logs.
- Only the read-only ground-truth prompts are sent. The run aborts after an API response signals `CREATE_TICKET`, escalation, or a ticket payload.
- Model judging and API calls cost tokens and may include answers/context previews in the configured provider request. Do not add PII to the dataset.
- Results are written to `eval/results/deepeval_live_<timestamp>.json` unless `--output-json` is supplied.
- The report includes the exact judge model, target URL/environment, latency, intent, citations, context previews, deterministic checks, DeepEval scores/reasons, and safety-abort state.

DeepEval is manual-only. It is not part of the normal test suite, CI, or deployment workflow.

# InsightAI Architecture

## Overview

```text
                         ┌──────────────────────┐
                         │  data/sales.csv      │
                         └──────────┬───────────┘
                                    │ validate and import
                                    ▼
                         ┌──────────────────────┐
                         │ database.py / SQLite │
                         │ transactions +       │
                         │ exclusion reasons    │
                         └──────────┬───────────┘
                                    │ SELECT queries
                                    ▼
┌────────────┐  HTTP POST /ask  ┌────────────────────┐
│ Streamlit  │ ───────────────► │ FastAPI (main.py)  │
│ app.py     │                  └─────────┬──────────┘
└──────▲─────┘                            │
       │                                  ▼
       │                        ┌────────────────────┐
       │                        │ ai_interpreter.py  │
       │                        │ optional Groq or   │
       │                        │ local fallback     │
       │                        └─────────┬──────────┘
       │                                  │ validated intent + parameters
       │                                  ▼
       │                        ┌────────────────────┐
       │                        │ analytics.py       │
       │                        │ allowlisted SELECT │
       │                        └─────────┬──────────┘
       │                                  │
       └──── JSON answer + evidence ◄─────┘
```

## Component responsibilities

1. **CSV ingestion (`database.py`)** — reads `data/sales.csv`, validates dates and required fields, records exclusion reasons, computes revenue for valid rows, and stores all source records in SQLite. Initialization rebuilds the transactions table.
2. **API (`main.py`)** — exposes `GET /health` and `POST /ask`. Pydantic constrains the question to 1–500 characters. Unsupported questions and validation errors are returned as HTTP 422.
3. **Question interpretation (`ai_interpreter.py`)** — uses Groq when `GROQ_API_KEY` is configured. Otherwise it uses a local rule-based interpreter. A Groq failure also triggers the local fallback. The intended output is a supported intent and parameters, not SQL or a numeric answer.
4. **Analytics (`analytics.py`)** — maps supported intents to analytical SELECT statements, restricts grouping columns to a hardcoded allowlist, uses bound parameters for user-supplied values, and formats answers from database results.
5. **UI (`app.py`)** — collects a question, calls the API, displays the answer and supporting data, plots rankings/trends, and exposes the SQL evidence for inspection.

## Request flow

1. The user enters a natural-language question in Streamlit.
2. Streamlit sends it to FastAPI at `/ask`.
3. The interpreter selects an allowed intent and parameters.
4. The analytics layer validates relevant parameters and executes an allowlisted SELECT query.
5. FastAPI returns JSON containing the intent, answer, result rows, SQL, parameters, and an explanatory note.
6. Streamlit renders the answer and supporting evidence.

## Data and revenue rules

Revenue is computed as:

`Quantity × Unit_price − Discount_amount`

Only records without an exclusion reason are used in analytical totals. The provided CSV contains 51 source rows, of which 48 are valid completed transactions. The source CSV does not identify a currency.

## Safety boundaries and limitations

- Users cannot submit arbitrary SQL through the API.
- Grouping expressions are selected from a fixed allowlist.
- Values are bound as SQL parameters when applicable.
- Groq output is parsed as JSON and checked against supported intent names; model-generated SQL and financial answers are not executed or trusted.
- The local interpreter supports common phrasings only; it is not a general natural-language query engine.
- Production use would require authentication, rate limits, monitoring, and appropriate database access controls.

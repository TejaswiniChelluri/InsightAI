# InsightAI — Mini AI Business Intelligence Assistant

**GET selection assessment:** a natural-language sales analytics application backed by validated data and read-only analytical queries.

InsightAI lets a user ask supported questions about the supplied sales CSV without writing SQL. Streamlit provides the interface, FastAPI exposes the `/ask` API, SQLite stores imported transactions, and a constrained interpreter maps questions to supported analytical intents. Groq is optional; a local rule-based interpreter is used when no API key is configured or the Groq call fails.

## Features

- Total revenue and valid completed-transaction count
- Average transaction value
- Top/bottom rankings by product, region, category, or sales channel
- Monthly revenue trend
- Comparison of two months
- Online-versus-Retail revenue comparison
- Data-quality/excluded-record summary
- Supporting data and read-only SQL evidence in the interface

The application is intentionally not unrestricted text-to-SQL: unsupported questions are rejected.

## Requirements

- Python 3.10 or newer
- Internet access to install Python packages
- Optional: a Groq API key for LLM-based question interpretation

## Run on Ubuntu/Linux

Run these commands from the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python database.py
uvicorn main:app --reload
```

Keep the API terminal running. Open a **second terminal** in the same project directory and run:

```bash
source .venv/bin/activate
streamlit run app.py
```

Open `http://localhost:8501` for the interface. FastAPI documentation is available at `http://127.0.0.1:8000/docs`; health check: `http://127.0.0.1:8000/health`.

FastAPI also initializes the database on startup. Running `python database.py` first is useful to check that the CSV can be imported successfully.

### Optional Groq configuration

Set the key in the same terminal from which you start Uvicorn:

```bash
export GROQ_API_KEY="your-key-here"
# Optional; this is the default model:
export GROQ_MODEL="openai/gpt-oss-120b"
uvicorn main:app --reload
```

Do not commit or share a real API key. Without `GROQ_API_KEY`, the local rule-based interpreter is used. If the Groq request fails, the interpreter attempts the local fallback. The LLM classifies the question; it does not generate SQL or provide the financial answer.

## API example

Request:

```http
POST /ask
Content-Type: application/json
```

```json
{"question": "Which product generated the highest revenue?"}
```

The response includes `intent`, `answer`, `data`, `sql`, `parameters`, and `note`. Empty, unsupported, or invalid questions return HTTP 422.

## Dataset and data-quality rules

Source file: `data/sales.csv`. The database is created at `data/sales.db`.

- 51 source rows are imported and retained for auditability.
- Dates are parsed from `DD-MM-YYYY` and stored as ISO dates.
- Revenue is `Quantity × Unit_price − Discount_amount`.
- Only records with no exclusion reason are included in analytics; status must be `Completed`.
- Invalid dates, non-completed status, missing required fields, non-positive or fractional quantities, missing/negative prices or discounts, discounts exceeding gross sales, and duplicate/missing transaction IDs are rejected from analytics and recorded with an exclusion reason.
- Re-importing clears and rebuilds the transactions table; it is not an append operation.
- The CSV does not specify a currency, so the app does not assume one.

Expected checks for the supplied CSV:

| Check | Expected result |
|---|---:|
| Source records | 51 |
| Valid completed transactions | 48 |
| Total valid revenue | 1,439,200 |
| Highest-revenue product | Monitor — 473,000 |
| Highest-revenue region | South — 411,200 |
| Highest-revenue month | May 2026 — 318,500 |

Known excluded examples: TXN0033 is returned, TXN0034 has zero quantity, and TXN0051 has a missing unit price.

## Example questions

- What is the total revenue?
- Which product generated the highest revenue?
- Show the bottom 3 regions by revenue.
- What is the monthly revenue trend?
- Compare January and February 2026.
- Compare online and retail sales.
- What is the average order value?
- How many transactions are valid?
- Show data quality issues.

Month names without a year are interpreted as 2026. Supported wording depends on the interpreter; arbitrary per-product filters and arbitrary CSV questions are not implemented.

## Safety and reliability

- The API accepts a question, not SQL.
- Query groupings are selected from a hardcoded allowlist.
- Values are passed through SQL parameters where applicable.
- Model output is checked against supported intent names and constrained parameters; it is never executed as SQL.
- Financial answers and supporting rows are calculated from SQLite results.
- Destructive database requests are rejected by the interpreter.

For deployment beyond this assessment, add authentication, rate limiting, operational monitoring, and a read-only database account.

## Tests

Run:

```bash
pytest -v
```

The test suite covers core totals, product and region rankings, monthly trend, month comparison, channel comparison, exclusion handling, question parsing, unsupported/destructive questions, unsafe grouping, zero-baseline month comparison, and API validation.

## Architecture and AI usage

- [Architecture overview](docs/architecture.md)
- [AI-assisted development report](docs/ai_usage_report.md)
- [Detailed architecture guide (Word)](docs/InsightAI_Architecture_Guide.docx)

## Limitations

- The app supports a fixed set of analytical intents rather than arbitrary text-to-SQL.
- The local fallback recognizes common phrasings and may reject unfamiliar wording.
- There is no conversational memory or user authentication.
- The supplied data has no currency metadata.
- SQLite is appropriate for this small assessment, not a high-concurrency production service.

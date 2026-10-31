# AI-Assisted Development and Runtime AI Report

## 1. AI-Related Runtime Behavior

InsightAI uses an optional Groq-powered language model to interpret a user's natural-language business question and classify it into a restricted JSON format containing an intent and its parameters. Supported intents include total revenue, transaction count, average transaction value, rankings, monthly trends, month comparisons, channel comparisons, and data-quality summaries.

The language model does not generate SQL queries or calculate financial results. Instead, the application validates the identified intent and parameters, executes a predefined analytical query against SQLite, and formats the response using the query results.

When `GROQ_API_KEY` is not configured, the application uses a local rule-based interpreter. If the Groq request or response parsing fails, the application attempts to use the local fallback.

## 2. AI-Assisted Development Disclosure

ChatGPT was used as a development assistant to support project planning, implementation structure, source-code improvements, API and database integration, error handling, documentation preparation, and test design.

AI-generated suggestions were used as development aids to help improve the implementation and identify potential issues. The application's analytical calculations were designed to remain deterministic and verifiable through database query results and automated tests.

The development-time use of ChatGPT is separate from the optional Groq integration used by the running application.

## 3. Data Validation and Debugging

The data ingestion logic in `database.py` retains source records and records exclusion reasons for transactions that do not qualify for analytics.

The following checks were performed against the supplied CSV dataset:

- **Source records:** 51 transactions imported.
- **Valid transactions:** 48 completed transactions included in analytics.
- **Returned transaction:** TXN0033 is marked as returned.
- **Invalid quantity:** TXN0034 has a quantity of zero.
- **Missing value:** TXN0051 has a missing unit price.
- **Total valid revenue:** 1,439,200.
- **Revenue formula:** Quantity × Unit Price − Discount Amount.

Automated tests in the `tests/` directory cover important revenue totals, product rankings, monthly comparisons, channel comparisons, data-exclusion counts, unsupported or destructive questions, input validation, and the zero-baseline month-comparison edge case.

These checks help identify incorrect calculations, invalid inputs, and unexpected application behavior.

## 4. Problems Encountered and Debugging

One challenge was validating the transaction data and ensuring that invalid or incomplete records did not affect analytical results. The dataset was checked against expected transaction counts, revenue calculations, product rankings, and monthly and channel comparisons. Automated tests were used to verify analytical functions, input validation, and API behavior.

Another challenge was controlling how natural-language questions were translated into database operations. Allowing unrestricted SQL generation could introduce unsafe or invalid queries. To address this, the application restricts the interpreter to supported intents and parameters and uses predefined SQL queries in the analytics layer.

The test suite provides repeatable checks for supported analyses and invalid requests, helping detect regressions when the implementation changes.

## 5. Safety and Reliability Choices

- The language model is restricted to intent classification and parameter extraction.
- Supported intent names and grouping columns are constrained by the application.
- SQL queries are constructed by the analytics code; user questions and language-model output are not executed directly as SQL.
- Numeric answers are derived from SQLite query results.
- Unsupported questions are rejected rather than answered speculatively.
- A local rule-based fallback is available when the Groq integration is unavailable or fails.

## 6. Current Limitations

- The local fallback recognizes common question phrasings but may not understand every way a question can be expressed.
- Only predefined analyses are supported; arbitrary filters and unrestricted questions about the CSV are not available.
- The application does not currently provide authentication or conversational memory.
- The dataset does not specify currency metadata, so the application does not assign a currency to revenue values.
- The SQLite implementation is intended for a small assessment rather than a high-concurrency production environment.

## 7. Possible Future Improvements

With one additional day of development, the project could be improved by:

- Adding explicit date-range and dimension filters.
- Asking clarification questions when a user's request is ambiguous.
- Improving natural-language interpretation, including support for more varied wording and multiple languages.
- Adding chart export and more interactive visualizations.
- Adding authentication and API rate limiting.
- Expanding integration tests with malformed CSV files and additional edge cases.
- Improving error messages and documenting more example questions with their expected outputs.

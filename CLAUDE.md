# FinancialAPIFlask

## Project Purpose
A Flask REST API providing 4 financial data endpoints for stock quotes, historical prices,
portfolio summaries, and currency conversion. Built as a learning project for Claude Code
best practices.

## Tech Stack
- **Python 3.11+**
- **Flask** — web framework
- **yfinance** — Yahoo Finance data (stock quotes, historical prices)
- **requests** — HTTP calls for currency conversion API
- **python-dotenv** — environment variable management

## Project Structure
```
FinancialAPIFlask/
├── CLAUDE.md               # This file — Claude instructions
├── .env                    # Secret keys (never commit)
├── .env.example            # Template for env vars (safe to commit)
├── .gitignore
├── requirements.txt
├── app.py                  # Flask app entry point
├── routes/
│   ├── __init__.py
│   ├── company.py          # GET /api/company/<symbol>
│   ├── market.py           # GET /api/market/<symbol>
│   ├── historical.py       # POST /api/historical
│   └── insights.py         # POST /api/insights
└── tests/
    ├── __init__.py
    └── test_endpoints.py
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET  | `/api/company/<symbol>` | Company profile (name, summary, sector, officers) |
| GET  | `/api/market/<symbol>` | Live market data (price, change, volume, state) |
| POST | `/api/historical` | OHLCV daily data for a symbol and date range |
| POST | `/api/insights` | Analytical insights derived from historical price data |

## Environment Variables
See `.env.example`. No API keys required — all data comes from yfinance (Yahoo Finance, free).

## Commands
```bash
# Install dependencies (use the project's venv)
pip install -r requirements.txt

# Run development server
python app.py

# Run tests
python -m pytest tests/ -v
```

## Conventions
- All responses use a consistent JSON envelope: `{ "success": bool, "data": ..., "error": str|null }`
- HTTP errors return appropriate status codes (400, 404, 500)
- Ticker symbols are uppercased automatically
- Dates must be in ISO format: YYYY-MM-DD
- Do NOT expose raw exception messages to API consumers — wrap in clean error responses
- Do NOT commit `.env` files

## Libraries to Prefer
- Use `yfinance` for all stock data (not paid APIs)
- Use Flask's built-in `jsonify` for all responses
- Use Python's built-in `math` for calculations (no numpy needed)

## Things to Avoid
- No authentication layer (out of scope for this learning project)
- No database (all data fetched live from APIs)
- No pandas-heavy transformations — keep it simple and readable

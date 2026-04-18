from flask import Blueprint, jsonify, request
from datetime import date

from services import finance_service

historical_bp = Blueprint("historical", __name__)


@historical_bp.route("/api/historical", methods=["POST"])
def get_historical_data():
    """
    POST /api/historical
    Returns daily OHLCV historical market data for a company symbol
    within a specified date range.

    Request body (JSON):
    {
        "symbol":     "AAPL",
        "start_date": "2024-01-01",
        "end_date":   "2024-03-31"
    }

    Fields returned per day:
        date, open, high, low, close, volume
    """
    body = request.get_json(silent=True)

    # --- Step 1: validate the body exists and has all required fields ---
    if not body:
        return jsonify({
            "success": False,
            "data": None,
            "error": "Request body must be JSON with 'symbol', 'start_date', and 'end_date'"
        }), 400

    symbol = str(body.get("symbol", "")).upper()
    start_str = body.get("start_date")
    end_str = body.get("end_date")

    if not symbol or not start_str or not end_str:
        return jsonify({
            "success": False,
            "data": None,
            "error": "All three fields are required: 'symbol', 'start_date', 'end_date'"
        }), 400

    # --- Step 2: validate date formats ---
    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except ValueError:
        return jsonify({
            "success": False,
            "data": None,
            "error": "Invalid date format. Use YYYY-MM-DD for both 'start_date' and 'end_date'"
        }), 400

    # --- Step 3: validate date range logic ---
    if start_date >= end_date:
        return jsonify({
            "success": False,
            "data": None,
            "error": "'start_date' must be earlier than 'end_date'"
        }), 400

    if end_date > date.today():
        return jsonify({
            "success": False,
            "data": None,
            "error": "'end_date' cannot be in the future"
        }), 400

    # --- Step 4: fetch and return the data ---
    try:
        df = finance_service.get_historical_prices(symbol, start_str, end_str)

        if df.empty:
            return jsonify({
                "success": False,
                "data": None,
                "error": f"No historical data found for '{symbol}' between {start_str} and {end_str}"
            }), 404

        # Convert each DataFrame row into a plain dict.
        # idx is a pandas Timestamp — .date() gives a clean date object,
        # str() converts it to "YYYY-MM-DD" for JSON serialisation.
        records = [
            {
                "date":   str(idx.date()),
                "open":   round(row["Open"],  4),
                "high":   round(row["High"],  4),
                "low":    round(row["Low"],   4),
                "close":  round(row["Close"], 4),
                "volume": int(row["Volume"]),
            }
            for idx, row in df.iterrows()
        ]

        return jsonify({
            "success": True,
            "data": {
                "symbol":     symbol,
                "start_date": start_str,
                "end_date":   end_str,
                "count":      len(records),
                "records":    records,
            },
            "error": None,
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "data": None,
            "error": "Failed to retrieve historical data"
        }), 500

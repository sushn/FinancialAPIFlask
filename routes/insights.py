import math
from datetime import date
from flask import Blueprint, jsonify, request

from services import finance_service

insights_bp = Blueprint("insights", __name__)

# Thresholds used to classify volatility into a human-readable band
VOLATILITY_LOW    = 15.0   # annualised % below which we call it "low"
VOLATILITY_HIGH   = 30.0   # annualised % above which we call it "high"

# Minimum rows needed to compute each moving average
SMA_20_MIN_ROWS = 20
SMA_50_MIN_ROWS = 50


@insights_bp.route("/api/insights", methods=["POST"])
def get_insights():
    """
    POST /api/insights
    Performs a comprehensive analysis of a company's historical price data
    and returns computed metrics alongside plain-English actionable insights.

    Request body (JSON):
    {
        "symbol":     "AAPL",
        "start_date": "2024-01-01",
        "end_date":   "2024-06-30"
    }

    Metrics returned:
        period_return_pct  — total % price change over the period
        volatility_pct     — annualised volatility (price risk)
        sma_20, sma_50     — simple moving averages of closing price
        trend              — BULLISH / BEARISH / NEUTRAL
        best_day           — date and % gain of the single best trading day
        worst_day          — date and % loss of the single worst trading day
        avg_volume         — average daily volume over the period
        insights           — list of plain-English summary statements
    """
    body = request.get_json(silent=True)

    # --- Step 1: validate body and required fields ---
    if not body:
        return jsonify({
            "success": False,
            "data": None,
            "error": "Request body must be JSON with 'symbol', 'start_date', and 'end_date'"
        }), 400

    symbol    = str(body.get("symbol", "")).upper()
    start_str = body.get("start_date")
    end_str   = body.get("end_date")

    if not symbol or not start_str or not end_str:
        return jsonify({
            "success": False,
            "data": None,
            "error": "All three fields are required: 'symbol', 'start_date', 'end_date'"
        }), 400

    # --- Step 2: validate date formats ---
    try:
        start_date = date.fromisoformat(start_str)
        end_date   = date.fromisoformat(end_str)
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

    # --- Step 4: fetch historical data ---
    try:
        df = finance_service.get_historical_prices(symbol, start_str, end_str)
    except Exception:
        return jsonify({
            "success": False,
            "data": None,
            "error": "Failed to fetch historical data from the market provider"
        }), 500

    if df.empty:
        return jsonify({
            "success": False,
            "data": None,
            "error": f"No historical data found for '{symbol}' between {start_str} and {end_str}"
        }), 404

    # --- Step 5: compute metrics ---
    closes  = df["Close"].tolist()       # list of daily closing prices
    volumes = df["Volume"].tolist()      # list of daily volumes
    dates   = [str(idx.date()) for idx in df.index]

    # 5a. Period return — how much did the price change overall?
    first_close = closes[0]
    last_close  = closes[-1]
    period_return_pct = round((last_close - first_close) / first_close * 100, 2)

    # 5b. Daily percentage changes — needed for volatility and best/worst day
    # pct_change[i] = (closes[i] - closes[i-1]) / closes[i-1] * 100
    daily_pct_changes = [
        (closes[i] - closes[i - 1]) / closes[i - 1] * 100
        for i in range(1, len(closes))
    ]

    # 5c. Annualised volatility — std of daily % changes scaled to a full year.
    # There are ~252 trading days in a year, so we multiply by sqrt(252).
    if len(daily_pct_changes) >= 2:
        mean   = sum(daily_pct_changes) / len(daily_pct_changes)
        variance = sum((x - mean) ** 2 for x in daily_pct_changes) / (len(daily_pct_changes) - 1)
        daily_std = math.sqrt(variance)
        volatility_pct = round(daily_std * math.sqrt(252), 2)
    else:
        volatility_pct = None

    # 5d. Simple moving averages of the most recent N closing prices
    sma_20 = round(sum(closes[-SMA_20_MIN_ROWS:]) / SMA_20_MIN_ROWS, 4) \
             if len(closes) >= SMA_20_MIN_ROWS else None
    sma_50 = round(sum(closes[-SMA_50_MIN_ROWS:]) / SMA_50_MIN_ROWS, 4) \
             if len(closes) >= SMA_50_MIN_ROWS else None

    # 5e. Trend — compare current price to the moving averages
    if sma_20 and sma_50:
        if last_close > sma_20 and last_close > sma_50:
            trend = "BULLISH"
        elif last_close < sma_20 and last_close < sma_50:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"
    else:
        trend = "INSUFFICIENT_DATA"

    # 5f. Best and worst single trading day in the period
    # daily_pct_changes[i] corresponds to dates[i+1] (since day 0 has no prior day)
    if daily_pct_changes:
        best_idx  = daily_pct_changes.index(max(daily_pct_changes))
        worst_idx = daily_pct_changes.index(min(daily_pct_changes))
        best_day  = {"date": dates[best_idx + 1],  "change_pct": round(daily_pct_changes[best_idx],  2)}
        worst_day = {"date": dates[worst_idx + 1], "change_pct": round(daily_pct_changes[worst_idx], 2)}
    else:
        best_day  = None
        worst_day = None

    # 5g. Average daily volume
    avg_volume = int(sum(volumes) / len(volumes)) if volumes else None

    # --- Step 6: build plain-English insight statements ---
    insights = []

    # Insight: overall return
    direction = "gained" if period_return_pct >= 0 else "lost"
    insights.append(
        f"{symbol} {direction} {abs(period_return_pct)}% "
        f"from {start_str} to {end_str}."
    )

    # Insight: volatility band
    if volatility_pct is not None:
        if volatility_pct < VOLATILITY_LOW:
            vol_label = "low"
        elif volatility_pct > VOLATILITY_HIGH:
            vol_label = "high"
        else:
            vol_label = "moderate"
        insights.append(
            f"Annualised volatility is {vol_label} at {volatility_pct}% — "
            f"reflecting {'stable' if vol_label == 'low' else 'elevated' if vol_label == 'high' else 'typical'} price swings."
        )

    # Insight: trend relative to moving averages
    if trend == "BULLISH":
        insights.append(
            f"Price (${round(last_close, 2)}) is above its 20-day SMA (${sma_20}) "
            f"and 50-day SMA (${sma_50}) — a bullish signal."
        )
    elif trend == "BEARISH":
        insights.append(
            f"Price (${round(last_close, 2)}) is below its 20-day SMA (${sma_20}) "
            f"and 50-day SMA (${sma_50}) — a bearish signal."
        )
    elif trend == "NEUTRAL":
        insights.append(
            f"Price (${round(last_close, 2)}) is between its 20-day SMA (${sma_20}) "
            f"and 50-day SMA (${sma_50}) — no clear directional trend."
        )
    else:
        insights.append(
            "Not enough data to compute moving averages — consider a wider date range."
        )

    # Insight: best and worst day
    if best_day:
        insights.append(
            f"Best single day: {best_day['date']} (+{best_day['change_pct']}%). "
            f"Worst single day: {worst_day['date']} ({worst_day['change_pct']}%)."
        )

    return jsonify({
        "success": True,
        "data": {
            "symbol":            symbol,
            "start_date":        start_str,
            "end_date":          end_str,
            "trading_days":      len(closes),
            "metrics": {
                "period_return_pct": period_return_pct,
                "volatility_pct":    volatility_pct,
                "sma_20":            sma_20,
                "sma_50":            sma_50,
                "trend":             trend,
                "best_day":          best_day,
                "worst_day":         worst_day,
                "avg_volume":        avg_volume,
            },
            "insights": insights,
        },
        "error": None,
    }), 200

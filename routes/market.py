from flask import Blueprint, jsonify

from services import finance_service

market_bp = Blueprint("market", __name__)


@market_bp.route("/api/market/<symbol>", methods=["GET"])
def get_market_data(symbol):
    """
    GET /api/market/<symbol>
    Returns real-time stock market data for a given company symbol.

    Fields returned:
        - market_state: current state of the market (REGULAR, PRE, POST, CLOSED)
        - current_price: latest traded price
        - previous_close: prior session's closing price
        - change: absolute price difference (current - previous_close)
        - change_pct: percentage price change
        - open, day_high, day_low: today's trading range
        - 52w_high, 52w_low: 52-week price range
        - volume, avg_volume: trading activity

    Example: GET /api/market/TSLA
    """
    symbol = symbol.upper()
    try:
        info = finance_service.get_market_info(symbol)

        # currentPrice or regularMarketPrice are the reliable live-price fields.
        # If neither is present the symbol is invalid or has no market data.
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not info or current_price is None:
            return jsonify({
                "success": False,
                "data": None,
                "error": f"Symbol '{symbol}' not found or market data unavailable"
            }), 404

        previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

        # Price change and percentage change are derived, not fetched directly.
        # Guard against a missing previous_close to avoid a ZeroDivisionError.
        if previous_close:
            change = round(current_price - previous_close, 4)
            change_pct = round((change / previous_close) * 100, 2)
        else:
            change = None
            change_pct = None

        data = {
            "symbol": symbol,
            "name": info.get("shortName"),
            "currency": info.get("currency"),
            "market_state": info.get("marketState"),
            "current_price": round(current_price, 4),
            "previous_close": round(previous_close, 4) if previous_close else None,
            "change": change,
            "change_pct": change_pct,
            "open": info.get("open") or info.get("regularMarketOpen"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "avg_volume": info.get("averageVolume"),
        }
        return jsonify({"success": True, "data": data, "error": None}), 200

    except Exception:
        return jsonify({
            "success": False,
            "data": None,
            "error": "Failed to retrieve market data"
        }), 500

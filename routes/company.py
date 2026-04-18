from flask import Blueprint, jsonify

from services import finance_service

company_bp = Blueprint("company", __name__)


@company_bp.route("/api/company/<symbol>", methods=["GET"])
def get_company_info(symbol):
    """
    GET /api/company/<symbol>
    Returns detailed company information for a given stock symbol.

    Fields returned:
        - symbol, full name, business summary
        - industry, sector
        - key officers (name and title)

    Example: GET /api/company/AAPL
    """
    symbol = symbol.upper()
    try:
        info = finance_service.get_company_info(symbol)

        # yfinance returns a minimal dict for unrecognised symbols.
        # longName is a reliable indicator that company data exists.
        if not info or not info.get("longName"):
            return jsonify({
                "success": False,
                "data": None,
                "error": f"Symbol '{symbol}' not found or no company data available"
            }), 404

        # companyOfficers is a list of dicts like:
        # {"name": "Timothy D. Cook", "title": "CEO & Director", ...}
        # We only surface name and title to keep the response clean.
        raw_officers = info.get("companyOfficers") or []
        officers = [
            {"name": officer.get("name"), "title": officer.get("title")}
            for officer in raw_officers
            if officer.get("name") and officer.get("title")
        ]

        data = {
            "symbol": symbol,
            "name": info.get("longName"),
            "summary": info.get("longBusinessSummary"),
            "industry": info.get("industry"),
            "sector": info.get("sector"),
            "website": info.get("website"),
            "country": info.get("country"),
            "employees": info.get("fullTimeEmployees"),
            "officers": officers,
        }
        return jsonify({"success": True, "data": data, "error": None}), 200

    except Exception:
        return jsonify({
            "success": False,
            "data": None,
            "error": "Failed to retrieve company information"
        }), 500

from flask import Flask, jsonify
from dotenv import load_dotenv

from routes.company import company_bp
from routes.market import market_bp
from routes.historical import historical_bp
from routes.insights import insights_bp

# Load environment variables from .env file before anything else
load_dotenv()

app = Flask(__name__)

# Register all route blueprints
app.register_blueprint(company_bp)
app.register_blueprint(market_bp)
app.register_blueprint(historical_bp)
app.register_blueprint(insights_bp)


@app.route("/", methods=["GET"])
def index():
    """Health check / API overview."""
    return jsonify({
        "name": "FinancialAPIFlask",
        "version": "1.0.0",
        "endpoints": [
            "GET  /api/company/<symbol>",
            "GET  /api/market/<symbol>",
            "POST /api/historical",
            "POST /api/insights",
        ],
    }), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "data": None, "error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"success": False, "data": None, "error": "Method not allowed"}), 405


if __name__ == "__main__":
    app.run(debug=True, port=5000)

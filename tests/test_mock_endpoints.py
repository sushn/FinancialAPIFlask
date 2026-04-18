import pandas as pd
import pytest

import services.finance_service as finance_service


pytestmark = pytest.mark.mock


def _build_history_frame():
    index = pd.to_datetime(
        [
            "2024-01-02",
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
        ]
    )
    return pd.DataFrame(
        {
            "Open": [100.0, 102.0, 101.0, 105.0],
            "High": [103.0, 104.0, 106.0, 107.0],
            "Low": [99.0, 100.0, 100.0, 104.0],
            "Close": [102.0, 101.0, 105.0, 106.0],
            "Volume": [1000, 1500, 1200, 1100],
        },
        index=index,
    )


def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["name"] == "FinancialAPIFlask"
    assert "endpoints" in data


def test_company_valid_symbol(client, monkeypatch):
    monkeypatch.setattr(
        finance_service,
        "get_company_info",
        lambda symbol: {
            "longName": "Apple Inc.",
            "longBusinessSummary": "Makes devices and services.",
            "industry": "Consumer Electronics",
            "sector": "Technology",
            "website": "https://www.apple.com",
            "country": "United States",
            "fullTimeEmployees": 161000,
            "companyOfficers": [
                {"name": "Tim Cook", "title": "CEO"},
                {"name": "Kevan Parekh", "title": "CFO"},
            ],
        },
    )

    resp = client.get("/api/company/AAPL")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "AAPL"
    assert data["data"]["name"] == "Apple Inc."
    assert len(data["data"]["officers"]) == 2


def test_company_invalid_symbol(client, monkeypatch):
    monkeypatch.setattr(finance_service, "get_company_info", lambda symbol: {})

    resp = client.get("/api/company/INVALID_TICKER_XYZ123")
    assert resp.status_code == 404

    data = resp.get_json()
    assert data["success"] is False


def test_market_valid_symbol(client, monkeypatch):
    monkeypatch.setattr(
        finance_service,
        "get_market_info",
        lambda symbol: {
            "shortName": "Apple Inc.",
            "currency": "USD",
            "marketState": "REGULAR",
            "currentPrice": 185.12,
            "previousClose": 183.0,
            "open": 184.0,
            "dayHigh": 186.0,
            "dayLow": 182.5,
            "fiftyTwoWeekHigh": 199.62,
            "fiftyTwoWeekLow": 164.08,
            "volume": 50000000,
            "averageVolume": 55000000,
        },
    )

    resp = client.get("/api/market/AAPL")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "AAPL"
    assert data["data"]["current_price"] == 185.12
    assert data["data"]["change_pct"] == 1.16


def test_market_invalid_symbol(client, monkeypatch):
    monkeypatch.setattr(finance_service, "get_market_info", lambda symbol: {})

    resp = client.get("/api/market/INVALID_TICKER_XYZ123")
    assert resp.status_code == 404

    data = resp.get_json()
    assert data["success"] is False


def test_historical_missing_body(client):
    resp = client.post("/api/historical", content_type="application/json")
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["success"] is False
    assert "request body" in data["error"].lower()


def test_historical_missing_fields(client):
    resp = client.post("/api/historical", json={"symbol": "AAPL"})
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["success"] is False
    assert "required" in data["error"].lower()


def test_historical_bad_date_format(client):
    resp = client.post(
        "/api/historical",
        json={
            "symbol": "AAPL",
            "start_date": "not-a-date",
            "end_date": "2024-01-31",
        },
    )
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["success"] is False
    assert "date format" in data["error"].lower()


def test_historical_start_after_end(client):
    resp = client.post(
        "/api/historical",
        json={
            "symbol": "AAPL",
            "start_date": "2024-12-01",
            "end_date": "2024-01-01",
        },
    )
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["success"] is False
    assert "earlier" in data["error"].lower()


def test_historical_success(client, monkeypatch):
    monkeypatch.setattr(
        finance_service,
        "get_historical_prices",
        lambda symbol, start_date, end_date: _build_history_frame(),
    )

    resp = client.post(
        "/api/historical",
        json={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "AAPL"
    assert data["data"]["count"] == 4
    assert data["data"]["records"][0]["date"] == "2024-01-02"


def test_insights_missing_body(client):
    resp = client.post("/api/insights", content_type="application/json")
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["success"] is False
    assert "request body" in data["error"].lower()


def test_insights_missing_fields(client):
    resp = client.post("/api/insights", json={"symbol": "AAPL"})
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["success"] is False
    assert "required" in data["error"].lower()


def test_insights_bad_date_format(client):
    resp = client.post(
        "/api/insights",
        json={
            "symbol": "AAPL",
            "start_date": "bad-date",
            "end_date": "2024-06-30",
        },
    )
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["success"] is False
    assert "date format" in data["error"].lower()


def test_insights_start_after_end(client):
    resp = client.post(
        "/api/insights",
        json={
            "symbol": "AAPL",
            "start_date": "2024-06-30",
            "end_date": "2024-01-01",
        },
    )
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["success"] is False
    assert "earlier" in data["error"].lower()


def test_insights_success(client, monkeypatch):
    monkeypatch.setattr(
        finance_service,
        "get_historical_prices",
        lambda symbol, start_date, end_date: _build_history_frame(),
    )

    resp = client.post(
        "/api/insights",
        json={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "AAPL"
    assert data["data"]["metrics"]["period_return_pct"] == 3.92
    assert data["data"]["metrics"]["trend"] == "INSUFFICIENT_DATA"
    assert len(data["data"]["insights"]) >= 3

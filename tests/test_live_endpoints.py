from datetime import date, timedelta

import pytest


pytestmark = pytest.mark.live


def test_live_company_endpoint(client):
    resp = client.get("/api/company/AAPL")
    assert resp.status_code in (200, 404, 500)

    data = resp.get_json()
    assert "success" in data
    assert "data" in data
    assert "error" in data


def test_live_market_endpoint(client):
    resp = client.get("/api/market/AAPL")
    assert resp.status_code in (200, 404, 500)

    data = resp.get_json()
    assert "success" in data
    assert "data" in data
    assert "error" in data


def test_live_historical_endpoint(client):
    end_date = date.today() - timedelta(days=5)
    start_date = end_date - timedelta(days=15)

    resp = client.post(
        "/api/historical",
        json={
            "symbol": "AAPL",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )
    assert resp.status_code in (200, 404, 500)

    data = resp.get_json()
    assert "success" in data
    assert "data" in data
    assert "error" in data


def test_live_insights_endpoint(client):
    end_date = date.today() - timedelta(days=5)
    start_date = end_date - timedelta(days=90)

    resp = client.post(
        "/api/insights",
        json={
            "symbol": "AAPL",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )
    assert resp.status_code in (200, 404, 500)

    data = resp.get_json()
    assert "success" in data
    assert "data" in data
    assert "error" in data

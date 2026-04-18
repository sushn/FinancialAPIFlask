def test_ui_page_renders(client):
    resp = client.get("/ui")

    assert resp.status_code == 200
    assert "text/html" in resp.content_type

    page = resp.get_data(as_text=True)
    assert "Financial API Playground" in page
    assert "/api/historical" in page
    assert "/api/insights" in page

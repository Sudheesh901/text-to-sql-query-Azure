from fastapi.testclient import TestClient

import api.main as main


client = TestClient(main.app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "beavelo-api",
    }


def test_query_success(monkeypatch):
    def mock_run_question(question):
        assert question == "Which customers are located in Germany?"
        return {
            "status": "success",
            "message": None,
            "sql": "SELECT * FROM customers WHERE country = 'Germany';",
            "columns": ["customer_id", "company_name", "country"],
            "rows": [
                {
                    "customer_id": "ALFKI",
                    "company_name": "Alfreds Futterkiste",
                    "country": "Germany",
                }
            ],
        }

    monkeypatch.setattr(main, "run_question", mock_run_question)

    response = client.post(
        "/v1/query",
        json={"question": "Which customers are located in Germany?"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["columns"] == ["customer_id", "company_name", "country"]
    assert len(body["rows"]) == 1


def test_query_returns_clarification(monkeypatch):
    monkeypatch.setattr(
        main,
        "run_question",
        lambda question: {
            "status": "clarification",
            "message": "Do you mean total quantity across all products?",
            "sql": None,
            "columns": [],
            "rows": [],
        },
    )

    response = client.post(
        "/v1/query",
        json={"question": "Show the top three customers and product names"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "clarification"
    assert "total quantity" in body["message"]


def test_query_returns_safe_error(monkeypatch):
    monkeypatch.setattr(
        main,
        "run_question",
        lambda question: {
            "status": "error",
            "message": "Only one read-only SELECT statement is allowed.",
            "sql": None,
            "columns": [],
            "rows": [],
        },
    )

    response = client.post(
        "/v1/query",
        json={"question": "Delete all customers"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "error"
    assert "SELECT" in body["message"]


def test_query_rejects_empty_question():
    response = client.post(
        "/v1/query",
        json={"question": ""},
    )

    assert response.status_code == 422


def test_cors_allows_streamlit_origin():
    response = client.options(
        "/v1/query",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:8501"
    )
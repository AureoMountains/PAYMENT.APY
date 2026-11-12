from decimal import Decimal


def payment_payload(**overrides):
    payload = {
        "amount": "100.00",
        "currency": "BRL",
        "method": "pix",
        "description": "Test payment",
        "customer_id": "customer-001"
    }

    payload.update(overrides)
    return payload


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_successful_payment(client, headers):
    response = client.put(
        "/payments/payment-001",
        json=payment_payload(),
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == "payment-001"
    assert data["status"] == "processed"
    assert Decimal(data["amount"]) == Decimal("100.00")
    assert Decimal(data["converted_amount"]) == Decimal("20.00")
    assert data["converted_currency"] == "USD"
    assert data["risk_flags"] == []


def test_high_amount_requires_review(client, headers):
    response = client.put(
        "/payments/payment-002",
        json=payment_payload(amount="6000.00"),
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "review"
    assert "HIGH_AMOUNT" in data["risk_flags"]


def test_unknown_payment_method(client, headers):
    response = client.put(
        "/payments/payment-003",
        json=payment_payload(method="cash"),
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "review"
    assert "UNKNOWN_METHOD" in data["risk_flags"]


def test_invalid_token(client):
    response = client.put(
        "/payments/payment-004",
        json=payment_payload(),
        headers={"X-Token": "wrong-token"}
    )

    assert response.status_code == 401


def test_missing_token(client):
    response = client.put(
        "/payments/payment-005",
        json=payment_payload()
    )

    assert response.status_code == 422


def test_invalid_amount(client, headers):
    response = client.put(
        "/payments/payment-006",
        json=payment_payload(amount="-10.00"),
        headers=headers
    )

    assert response.status_code == 422


def test_unsupported_currency(client, headers):
    response = client.put(
        "/payments/payment-007",
        json=payment_payload(currency="JPY"),
        headers=headers
    )

    assert response.status_code == 422


def test_duplicate_payment_id(client, headers):
    first = client.put(
        "/payments/payment-008",
        json=payment_payload(),
        headers=headers
    )

    second = client.put(
        "/payments/payment-008",
        json=payment_payload(amount="200.00"),
        headers=headers
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_idempotency_returns_original_payment(client, headers):
    headers["X-Idempotency-Key"] = "operation-001"

    first = client.put(
        "/payments/payment-009",
        json=payment_payload(),
        headers=headers
    )

    second = client.put(
        "/payments/payment-010",
        json=payment_payload(),
        headers=headers
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json() == second.json()
    assert second.json()["payment_id"] == "payment-009"


def test_idempotency_rejects_different_payload(client, headers):
    headers["X-Idempotency-Key"] = "operation-002"

    first = client.put(
        "/payments/payment-011",
        json=payment_payload(amount="100.00"),
        headers=headers
    )

    second = client.put(
        "/payments/payment-012",
        json=payment_payload(amount="200.00"),
        headers=headers
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_payment_persists_after_request(client, headers):
    first = client.put(
        "/payments/payment-013",
        json=payment_payload(),
        headers=headers
    )

    second = client.put(
        "/payments/payment-013",
        json=payment_payload(),
        headers=headers
    )

    assert first.status_code == 200
    assert second.status_code == 409

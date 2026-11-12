import hashlib
import json

from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Payment, IdempotencyRecord
from app.schemas import PaymentRequest, PaymentResponse
from app.services.risk import assess_risk


EXCHANGE_RATES = {
    "BRL": Decimal("0.20"),
    "EUR": Decimal("1.10"),
    "USD": Decimal("1.00")
}


def convert_to_usd(
    amount: Decimal,
    currency: str
) -> Decimal:

    rate = EXCHANGE_RATES.get(currency)

    if rate is None:
        raise HTTPException(
            status_code=422,
            detail="Unsupported currency"
        )

    return (amount * rate).quantize(Decimal("0.01"))


def generate_request_hash(payload: PaymentRequest) -> str:
    serialized = json.dumps(
        payload.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def to_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        payment_id=payment.payment_id,
        status=payment.status,
        processed_at=payment.processed_at,
        amount=Decimal(payment.amount),
        currency=payment.currency,
        method=payment.method,
        description=payment.description,
        converted_amount=Decimal(payment.converted_amount),
        converted_currency=payment.converted_currency,
        risk_flags=payment.risk_flags
    )


def process_payment(
    db: Session,
    payment_id: str,
    payload: PaymentRequest,
    idempotency_key: str | None = None
) -> PaymentResponse:

    request_hash = generate_request_hash(payload)

    # 1. Check idempotency
    if idempotency_key:
        existing_record = db.get(
            IdempotencyRecord,
            idempotency_key
        )

        if existing_record:
            if existing_record.request_hash != request_hash:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key reused with different request"
                )

            existing_payment = db.get(
                Payment,
                existing_record.payment_id
            )

            if existing_payment is None:
                raise HTTPException(
                    status_code=500,
                    detail="Inconsistent idempotency record"
                )

            return to_response(existing_payment)

    # 2. Prevent duplicate payment identifiers
    if db.get(Payment, payment_id):
        raise HTTPException(
            status_code=409,
            detail="Payment ID already exists"
        )

    # 3. Fraud assessment
    risk_flags = assess_risk(payload)

    # 4. Currency conversion
    converted_amount = convert_to_usd(
        payload.amount,
        payload.currency
    )

    # 5. Create payment record
    payment = Payment(
        payment_id=payment_id,
        status="review" if risk_flags else "processed",
        processed_at=datetime.now(timezone.utc),
        amount=str(payload.amount),
        currency=payload.currency,
        method=payload.method,
        description=payload.description,
        customer_id=payload.customer_id,
        converted_amount=str(converted_amount),
        converted_currency="USD",
        risk_flags=risk_flags
    )

    db.add(payment)

    # 6. Persist idempotency record
    if idempotency_key:
        db.add(
            IdempotencyRecord(
                key=idempotency_key,
                request_hash=request_hash,
                payment_id=payment_id
            )
        )

    try:
        db.commit()
        db.refresh(payment)

    except Exception:
        db.rollback()
        raise

    return to_response(payment)

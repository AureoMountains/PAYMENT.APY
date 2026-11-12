from datetime import datetime

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[str] = mapped_column(
        String(128),
        primary_key=True
    )

    status: Mapped[str] = mapped_column(String(20), nullable=False)

    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    amount: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    method: Mapped[str] = mapped_column(String(50), nullable=False)

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    customer_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True
    )

    converted_amount: Mapped[str] = mapped_column(
        String(32),
        nullable=False
    )

    converted_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False
    )

    risk_flags: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False
    )


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    key: Mapped[str] = mapped_column(
        String(255),
        primary_key=True
    )

    request_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    payment_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False
    )

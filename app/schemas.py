from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


Currency = Literal["BRL", "EUR", "USD"]


class PaymentRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2
    )

    currency: Currency

    method: str = Field(
        min_length=1,
        max_length=50
    )

    description: str | None = Field(
        default=None,
        max_length=500
    )

    customer_id: str | None = Field(
        default=None,
        max_length=128
    )


class PaymentResponse(BaseModel):
    payment_id: str
    status: Literal["processed", "review"]
    processed_at: datetime

    amount: Decimal
    currency: str

    method: str
    description: str | None

    converted_amount: Decimal
    converted_currency: str

    risk_flags: list[str]

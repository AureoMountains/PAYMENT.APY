from app.schemas import PaymentRequest


SUPPORTED_METHODS = {
    "credit_card",
    "pix",
    "debit",
    "paypal"
}


def assess_risk(data: PaymentRequest) -> list[str]:
    flags = []

    if data.amount > 5000:
        flags.append("HIGH_AMOUNT")

    if data.method not in SUPPORTED_METHODS:
        flags.append("UNKNOWN_METHOD")

    return flags

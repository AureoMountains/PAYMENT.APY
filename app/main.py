from contextlib import asynccontextmanager
from collections.abc import Generator

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, create_database
from app.schemas import PaymentRequest, PaymentResponse
from app.security import require_token
from app.services.payments import process_payment


def create_app(
    database_url: str | None = None,
    api_token: str | None = None
) -> FastAPI:

    settings = get_settings() if api_token is None or database_url is None else None

    token = api_token or settings.api_token
    db_url = database_url or settings.database_url

    engine, SessionLocal = create_database(db_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(bind=engine)
        yield
        engine.dispose()

    app = FastAPI(
        title="Payment Processing API",
        description="Educational payment processing simulator.",
        version="1.0.0",
        lifespan=lifespan
    )

    def get_db() -> Generator[Session, None, None]:
        db = SessionLocal()

        try:
            yield db
        finally:
            db.close()

    def authenticate(
        x_token: str = Header(..., alias="X-Token")
    ) -> None:
        require_token(
            x_token=x_token,
            expected_token=token
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.put(
        "/payments/{payment_id}",
        response_model=PaymentResponse,
        dependencies=[Depends(authenticate)]
    )
    def create_payment(
        payment_id: str,
        payload: PaymentRequest,
        x_idempotency_key: str | None = Header(
            default=None,
            alias="X-Idempotency-Key"
        ),
        db: Session = Depends(get_db)
    ):
        if not payment_id.strip():
            raise HTTPException(
                status_code=422,
                detail="Invalid payment ID"
            )

        if x_idempotency_key is not None:
            if not x_idempotency_key.strip() or len(x_idempotency_key) > 255:
                raise HTTPException(
                    status_code=422,
                    detail="Invalid idempotency key"
                )

        return process_payment(
            db=db,
            payment_id=payment_id,
            payload=payload,
            idempotency_key=x_idempotency_key
        )

    return app


app = create_app()

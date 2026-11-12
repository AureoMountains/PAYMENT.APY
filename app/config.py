import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_token: str
    database_url: str


def get_settings() -> Settings:
    token = os.getenv("API_TOKEN")

    if not token:
        raise RuntimeError("API_TOKEN environment variable is required")

    return Settings(
        api_token=token,
        database_url=os.getenv(
            "DATABASE_URL",
            "sqlite:///./payments.db"
        )
    )

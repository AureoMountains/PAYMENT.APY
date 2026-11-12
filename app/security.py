import secrets

from fastapi import Header, HTTPException, status


def require_token(
    x_token: str = Header(..., alias="X-Token"),
    expected_token: str = ""
) -> None:

    if not secrets.compare_digest(x_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

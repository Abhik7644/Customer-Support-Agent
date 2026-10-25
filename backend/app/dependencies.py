from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from backend.app.auth import decode_access_token
from backend.app.database import run_query

security = HTTPBearer()


def get_current_customer_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """
    Extracts and validates the JWT from the Authorization header.

    HTTPBearer (rather than OAuth2PasswordBearer) is used here because
    our /auth/login endpoint takes JSON (email + password), not the
    OAuth2 form-encoded 'username' field that OAuth2PasswordBearer's
    Swagger integration expects. HTTPBearer just expects a raw bearer
    token and doesn't assume anything about how that token was
    obtained - it matches our actual login flow correctly.
    """
    token = credentials.credentials
    try:
        return decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )


def get_current_admin_id(customer_id: int = Depends(get_current_customer_id)) -> int:
    """
    Reuses the existing JWT-based auth, then additionally checks the
    is_admin flag. Any endpoint using this instead of
    get_current_customer_id requires BOTH a valid token AND admin
    status - not a separate auth system, just an extra gate layered on
    top of the one you already have.
    """
    rows = run_query("SELECT is_admin FROM customers WHERE customer_id = %s;", (customer_id,))
    if not rows or not rows[0]["is_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return customer_id
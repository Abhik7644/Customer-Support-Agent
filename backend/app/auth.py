import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from backend.app.config import settings
from backend.app.database import run_query, run_write


def hash_password(password: str) -> str:
    """Hash a plain-text password. Never store the raw password anywhere."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a login attempt's password against the stored hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(customer_id: int) -> str:
    """
    Create a signed JWT containing the customer's ID.

    'sub' (subject) is the standard JWT claim for "who this token
    represents" - using the standard claim name means our tokens are
    interoperable with standard JWT tooling/libraries, not a bespoke
    shape only our own code understands.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(customer_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    """
    Verify a JWT's signature and expiration, and return the customer_id
    it represents.

    Raises jwt.InvalidTokenError (or a subclass) if the token is
    invalid, expired, or tampered with - the caller is responsible for
    turning that into an appropriate HTTP error.
    """
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    return int(payload["sub"])


def register_customer(name: str, email: str, password: str) -> int:
    """Create a new customer with a hashed password. Returns the new customer_id."""
    password_hash = hash_password(password)
    customer_id = run_write(
        """
        INSERT INTO customers (name, email, password_hash)
        VALUES (%s, %s, %s)
        RETURNING customer_id;
        """,
        (name, email, password_hash),
    )
    return customer_id


def authenticate_customer(email: str, password: str) -> int | None:
    """
    Verify email + password against stored data.
    Returns the customer_id on success, None on failure.
    """
    rows = run_query(
        "SELECT customer_id, password_hash FROM customers WHERE email = %s;",
        (email,),
    )
    if not rows:
        return None

    customer = rows[0]
    if customer["password_hash"] is None:
        return None  # seed customer with no password set yet

    if not verify_password(password, customer["password_hash"]):
        return None

    return customer["customer_id"]
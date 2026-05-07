"""Signed token generation and verification for email confirmation."""

from django.conf import settings
from django.core import signing

_SALT = "accounts-email-verification"


def make_verification_token(user) -> str:
    """Create a time-limited signed token encoding the user's primary key."""
    return signing.dumps({"user_id": user.pk}, salt=_SALT)


def verify_verification_token(token: str):
    """Decode *token* and return the user ID, or ``None`` if invalid/expired."""
    max_age = getattr(settings, "VERIFICATION_TOKEN_MAX_AGE", 86400)
    try:
        data = signing.loads(token, salt=_SALT, max_age=max_age)
        return data["user_id"]
    except signing.SignatureExpired:
        return None
    except signing.BadSignature:
        return None
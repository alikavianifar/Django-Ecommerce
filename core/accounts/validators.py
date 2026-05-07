"""Custom field validators for the accounts app."""

import phonenumbers
from django.core.exceptions import ValidationError


def validate_phone_number(value):
    """Validate that *value* is a syntactically correct phone number."""
    try:
        phone_number = phonenumbers.parse(value)
        if not phonenumbers.is_valid_number(phone_number):
            raise ValidationError("Enter a valid phone number.")
    except phonenumbers.phonenumberutil.NumberParseException:
        raise ValidationError("Enter a valid phone number.")

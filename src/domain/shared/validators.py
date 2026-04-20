import re


def validate_email(value: str) -> str:
    """Reusable email validator. Use inside Pydantic @field_validator."""
    value = value.strip().lower()
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
        raise ValueError("Invalid email address")
    if len(value) > 160:
        raise ValueError("Email must be 160 characters or less")
    return value


def validate_url(value: str) -> str:
    """Validates and normalizes URL. Prepends https:// if scheme absent."""
    value = value.strip()
    if not value:
        raise ValueError("URL cannot be blank")
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    if not re.match(r"https?://[^\s/$.?#].[^\s]*", value):
        raise ValueError("Invalid URL")
    return value


def validate_not_blank(value: str) -> str:
    """Trims whitespace and ensures value is not empty."""
    value = value.strip()
    if not value:
        raise ValueError("Field cannot be blank")
    return value

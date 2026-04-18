import pytest

from src.domain.shared.domain_validators import validate_email, validate_url, validate_not_blank


# ── validate_email ────────────────────────────────────────────────────────────

def test_validate_email_returns_stripped_lowercase():
    result = validate_email("  User@Example.COM  ")
    assert result == "user@example.com"


def test_validate_email_valid_address_passes():
    result = validate_email("alice@example.org")
    assert result == "alice@example.org"


def test_validate_email_missing_at_sign_raises():
    with pytest.raises(ValueError, match="Invalid email"):
        validate_email("notanemail.com")


def test_validate_email_missing_domain_raises():
    with pytest.raises(ValueError, match="Invalid email"):
        validate_email("user@")


def test_validate_email_missing_tld_raises():
    with pytest.raises(ValueError, match="Invalid email"):
        validate_email("user@domain")


def test_validate_email_exceeds_160_chars_raises():
    long_local = "a" * 155
    email = f"{long_local}@x.com"
    with pytest.raises(ValueError, match="160 characters"):
        validate_email(email)


def test_validate_email_exactly_160_chars_passes():
    # Build an email that is exactly 160 characters after strip+lower
    domain = "@example.com"
    local = "a" * (160 - len(domain))
    email = local + domain
    assert len(email) == 160
    result = validate_email(email)
    assert len(result) == 160


# ── validate_url ──────────────────────────────────────────────────────────────

def test_validate_url_prepends_https_when_scheme_absent():
    result = validate_url("example.com")
    assert result == "https://example.com"


def test_validate_url_keeps_existing_https_scheme():
    result = validate_url("https://example.com")
    assert result == "https://example.com"


def test_validate_url_keeps_existing_http_scheme():
    result = validate_url("http://example.com/path")
    assert result == "http://example.com/path"


def test_validate_url_strips_leading_whitespace():
    result = validate_url("  https://example.com  ")
    assert result == "https://example.com"


def test_validate_url_blank_string_raises():
    with pytest.raises(ValueError, match="blank"):
        validate_url("   ")


def test_validate_url_empty_string_raises():
    with pytest.raises(ValueError, match="blank"):
        validate_url("")


# ── validate_not_blank ────────────────────────────────────────────────────────

def test_validate_not_blank_returns_stripped_value():
    result = validate_not_blank("  hello  ")
    assert result == "hello"


def test_validate_not_blank_non_empty_passes():
    result = validate_not_blank("something")
    assert result == "something"


def test_validate_not_blank_whitespace_only_raises():
    with pytest.raises(ValueError, match="blank"):
        validate_not_blank("   ")


def test_validate_not_blank_empty_string_raises():
    with pytest.raises(ValueError, match="blank"):
        validate_not_blank("")

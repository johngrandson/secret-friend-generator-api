import secrets


def generate_group_token() -> str:
    """Generate a URL-safe random token for group links."""
    return secrets.token_urlsafe(16)

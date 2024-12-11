import secrets


class Hasher:
    @staticmethod
    def generate_group_token():
        return secrets.token_urlsafe(16)

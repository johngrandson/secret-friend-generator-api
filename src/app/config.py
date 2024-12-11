import logging
import os
from urllib import parse
from typing import List
from pydantic import BaseModel

from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings

log = logging.getLogger(__name__)


class BaseConfigurationModel(BaseModel):
    """Base configuration model used by all config options."""

    pass


def get_env_tags(tag_list: List[str]) -> dict:
    """Create dictionary of available env tags."""
    tags = {}
    for t in tag_list:
        tag_key, env_key = t.split(":")

        env_value = os.environ.get(env_key)

        if env_value:
            tags.update({tag_key: env_value})

    return tags


config = Config(".env")

from starlette.datastructures import Secret

LOG_LEVEL = config("LOG_LEVEL", default=logging.WARNING)
ENV = config("ENV", default="local")

ENV_TAG_LIST = config("ENV_TAGS", cast=CommaSeparatedStrings, default="")
ENV_TAGS = get_env_tags(ENV_TAG_LIST)

APP_UI_URL = config("APP_UI_URL", default="http://localhost:8080")
APP_ENCRYPTION_KEY = config("APP_ENCRYPTION_KEY", cast=Secret)

# authentication
VITE_APP_AUTH_REGISTRATION_ENABLED = config(
    "VITE_APP_AUTH_REGISTRATION_ENABLED", default="true"
)
APP_AUTH_REGISTRATION_ENABLED = VITE_APP_AUTH_REGISTRATION_ENABLED != "false"


APP_AUTHENTICATION_PROVIDER_SLUG = config(
    "APP_AUTHENTICATION_PROVIDER_SLUG", default="APP-auth-provider-basic"
)

MJML_PATH = config(
    "MJML_PATH",
    default=f"{os.path.dirname(os.path.realpath(__file__))}/static/APP/node_modules/.bin",
)
APP_MARKDOWN_IN_INCIDENT_DESC = config(
    "APP_MARKDOWN_IN_INCIDENT_DESC", cast=bool, default=False
)
APP_ESCAPE_HTML = config("APP_ESCAPE_HTML", cast=bool, default=None)
if APP_ESCAPE_HTML and APP_MARKDOWN_IN_INCIDENT_DESC:
    log.warning(
        "HTML escape and Markdown are both explicitly enabled, this may cause unexpected notification markup."
    )
elif APP_ESCAPE_HTML is None and APP_MARKDOWN_IN_INCIDENT_DESC:
    log.info("Disabling HTML escaping, due to Markdown was enabled explicitly.")
    APP_ESCAPE_HTML = False

APP_JWT_AUDIENCE = config("APP_JWT_AUDIENCE", default=None)
APP_JWT_EMAIL_OVERRIDE = config("APP_JWT_EMAIL_OVERRIDE", default=None)

if APP_AUTHENTICATION_PROVIDER_SLUG == "APP-auth-provider-pkce":
    if not APP_JWT_AUDIENCE:
        log.warn("No JWT Audience specified. This is required for IdPs like Okta")
    if not APP_JWT_EMAIL_OVERRIDE:
        log.warn("No JWT Email Override specified. 'email' is expected in the idtoken.")

APP_JWT_SECRET = config("APP_JWT_SECRET", default=None)
APP_JWT_ALG = config("APP_JWT_ALG", default="HS256")
APP_JWT_EXP = config("APP_JWT_EXP", cast=int, default=86400)  # Seconds

if APP_AUTHENTICATION_PROVIDER_SLUG == "APP-auth-provider-basic":
    if not APP_JWT_SECRET:
        log.warn(
            "No JWT secret specified, this is required if you are using basic authentication."
        )

APP_AUTHENTICATION_DEFAULT_USER = config(
    "APP_AUTHENTICATION_DEFAULT_USER", default="APP@example.com"
)

APP_AUTHENTICATION_PROVIDER_PKCE_JWKS = config(
    "APP_AUTHENTICATION_PROVIDER_PKCE_JWKS", default=None
)

APP_PKCE_DONT_VERIFY_AT_HASH = config("APP_PKCE_DONT_VERIFY_AT_HASH", default=False)

if APP_AUTHENTICATION_PROVIDER_SLUG == "APP-auth-provider-pkce":
    if not APP_AUTHENTICATION_PROVIDER_PKCE_JWKS:
        log.warn(
            "No PKCE JWKS url provided, this is required if you are using PKCE authentication."
        )

APP_AUTHENTICATION_PROVIDER_HEADER_NAME = config(
    "APP_AUTHENTICATION_PROVIDER_HEADER_NAME", default="remote-user"
)

# sentry middleware
SENTRY_ENABLED = config("SENTRY_ENABLED", default="")
SENTRY_DSN = config("SENTRY_DSN", default="")
SENTRY_APP_KEY = config("SENTRY_APP_KEY", default="")
SENTRY_TAGS = config("SENTRY_TAGS", default="")

# Frontend configuration
VITE_APP_AUTHENTICATION_PROVIDER_SLUG = APP_AUTHENTICATION_PROVIDER_SLUG

VITE_SENTRY_ENABLED = SENTRY_ENABLED
VITE_SENTRY_DSN = SENTRY_DSN
VITE_SENTRY_APP_KEY = SENTRY_APP_KEY
VITE_SENTRY_TAGS = SENTRY_TAGS

# used by pkce authprovider
VITE_APP_AUTHENTICATION_PROVIDER_PKCE_OPEN_ID_CONNECT_URL = config(
    "VITE_APP_AUTHENTICATION_PROVIDER_PKCE_OPEN_ID_CONNECT_URL", default=""
)
VITE_APP_AUTHENTICATION_PROVIDER_PKCE_CLIENT_ID = config(
    "APP_AUTHENTICATION_PROVIDER_PKCE_CLIENT_ID", default=""
)
VITE_APP_AUTHENTICATION_PROVIDER_USE_ID_TOKEN = config(
    "APP_AUTHENTICATION_PROVIDER_USE_ID_TOKEN", default=""
)

# static files
DEFAULT_STATIC_DIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    os.path.join("static", "APP", "dist"),
)
STATIC_DIR = config("STATIC_DIR", default=DEFAULT_STATIC_DIR)

# metrics
METRIC_PROVIDERS = config("METRIC_PROVIDERS", cast=CommaSeparatedStrings, default="")

# database
DATABASE_HOSTNAME = config("DATABASE_HOSTNAME")
DATABASE_CREDENTIALS = config("DATABASE_CREDENTIALS", cast=Secret)
# this will support special chars for credentials
_DATABASE_CREDENTIAL_USER, _DATABASE_CREDENTIAL_PASSWORD = str(
    DATABASE_CREDENTIALS
).split(":")
_QUOTED_DATABASE_PASSWORD = parse.quote(str(_DATABASE_CREDENTIAL_PASSWORD))
DATABASE_NAME = config("DATABASE_NAME", default="APP")
DATABASE_PORT = config("DATABASE_PORT", default="5432")
DATABASE_ENGINE_POOL_SIZE = config("DATABASE_ENGINE_POOL_SIZE", cast=int, default=20)
DATABASE_ENGINE_MAX_OVERFLOW = config(
    "DATABASE_ENGINE_MAX_OVERFLOW", cast=int, default=0
)
# Deal with DB disconnects
# https://docs.sqlalchemy.org/en/20/core/pooling.html#pool-disconnects
DATABASE_ENGINE_POOL_PING = config("DATABASE_ENGINE_POOL_PING", default=False)
SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{_DATABASE_CREDENTIAL_USER}:{_QUOTED_DATABASE_PASSWORD}@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"

ALEMBIC_CORE_REVISION_PATH = config(
    "ALEMBIC_CORE_REVISION_PATH",
    default=f"{os.path.dirname(os.path.realpath(__file__))}/database/revisions/core",
)
ALEMBIC_TENANT_REVISION_PATH = config(
    "ALEMBIC_TENANT_REVISION_PATH",
    default=f"{os.path.dirname(os.path.realpath(__file__))}/database/revisions/tenant",
)
ALEMBIC_INI_PATH = config(
    "ALEMBIC_INI_PATH",
    default=f"{os.path.dirname(os.path.realpath(__file__))}/alembic.ini",
)
ALEMBIC_MULTI_TENANT_MIGRATION_PATH = config(
    "ALEMBIC_MULTI_TENANT_MIGRATION_PATH",
    default=f"{os.path.dirname(os.path.realpath(__file__))}/database/revisions/multi-tenant-migration.sql",
)

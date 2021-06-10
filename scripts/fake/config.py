"""Set any relevant config options."""

from os import getenv

from django.utils.functional import classproperty
from scripts.fake import arguments


class PostgreSQL:
    """Pull postgres connection info from the environment."""

    USER: str = getenv("SQL_USER", "")
    HOST: str = getenv("SQL_HOST", "")
    PORT: str = getenv("SQL_PORT", "")
    DATABASE: str = getenv("SQL_DATABASE", "")
    PASSWORD: str = getenv("SQL_PASSWORD", "")

    @classproperty
    def dsn(cls) -> str:
        return f"postgres://{cls.USER}:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.DATABASE}"


USERS, CATEGORIES, TEAMS, CHALLENGES, SOLVES = (
    int(arguments.get(f"--{param}", "0")) for param in ("users", "categories", "teams", "challenges", "solves")
)
FORCE = arguments.get("--force")

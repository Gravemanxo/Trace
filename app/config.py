import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./timekeeper.db")
    timezone_name: str = os.getenv("TIMEZONE", "Europe/Berlin")
    auth_enabled: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    auth_username: str = os.getenv("AUTH_USERNAME", "admin")
    auth_password: str = os.getenv("AUTH_PASSWORD", "change-me")
    csrf_cookie_name: str = "arbeitsraum_csrf"

    def validate(self) -> None:
        if self.auth_enabled and self.auth_password in {"", "change-me"}:
            raise RuntimeError(
                "AUTH_PASSWORD muss bei aktiviertem Basisschutz sicher gesetzt sein."
            )

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone_name)


settings = Settings()

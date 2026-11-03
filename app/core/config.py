"""Application settings, read from environment variables with safe development defaults."""
import os
from dataclasses import dataclass, field


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    # PostgreSQL in production, e.g. postgresql+psycopg://user:pass@host/hap. SQLite is the local default.
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./hap.db"))
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "dev-only-secret-change-me-in-production-32b"))
    jwt_minutes: int = field(default_factory=lambda: int(os.getenv("JWT_MINUTES", "30")))
    bcrypt_rounds: int = field(default_factory=lambda: int(os.getenv("BCRYPT_ROUNDS", "12")))
    lockout_attempts: int = 5
    lockout_minutes: int = 15
    # base64-encoded 32-byte key for AES-256-GCM (HAP-SR-006). Derived from jwt_secret if unset (dev only).
    data_key: str = field(default_factory=lambda: os.getenv("HAP_DATA_KEY", ""))
    admin_email: str = field(default_factory=lambda: os.getenv("ADMIN_EMAIL", "admin@hap.local"))
    admin_password: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", "Admin@1234"))
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", ""))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "1025")))
    mail_from: str = field(default_factory=lambda: os.getenv("MAIL_FROM", "no-reply@hap.local"))
    enable_scheduler: bool = field(default_factory=lambda: _bool("ENABLE_SCHEDULER", False))
    login_rate_per_minute: int = field(default_factory=lambda: int(os.getenv("LOGIN_RATE_PER_MINUTE", "10")))


settings = Settings()


def reload_settings() -> Settings:
    """Re-read environment variables (used by tests)."""
    global settings
    fresh = Settings()
    settings.__dict__.update(fresh.__dict__)
    return settings

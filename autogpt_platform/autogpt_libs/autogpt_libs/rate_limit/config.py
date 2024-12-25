from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RateLimitSettings(BaseSettings):
    redis_host: str = Field(
        default="redis://localhost:6379",
        description="Redis host",
        validation_alias="REDIS_HOST",
    )

    redis_port: str = Field(
        default="6379", description="Redis port", validation_alias="REDIS_PORT"
    )

    redis_password: str = Field(
        default="password",
        description="Redis password",
        validation_alias="REDIS_PASSWORD",
    )

    requests_per_minute: int = Field(
        default=60,
        description="Maximum number of requests allowed per minute per API key",
        validation_alias="RATE_LIMIT_REQUESTS_PER_MINUTE",
    )

    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")


RATE_LIMIT_SETTINGS = RateLimitSettings()
def get_redis_url() -> str:
    """
    Redis URL'sini döndürür.
    """
    return f"{RATE_LIMIT_SETTINGS.redis_host}:{RATE_LIMIT_SETTINGS.redis_port}"

def is_rate_limited(api_key: str) -> bool:
    """
    Belirtilen API anahtarı için oran sınırlamasının aşılıp aşılmadığını kontrol eder.
    """
    # Bu işlevin tam uygulanması Redis bağlantısı ve oran sınırlama mantığı gerektirir.
    # Bu sadece bir şablondur.
    return False
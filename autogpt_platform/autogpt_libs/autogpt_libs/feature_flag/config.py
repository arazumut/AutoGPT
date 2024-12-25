from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Ayarlar(BaseSettings):
    launch_darkly_sdk_anahtari: str = Field(
        default="",
        description="Launch Darkly SDK anahtarı",
        validation_alias="LAUNCH_DARKLY_SDK_KEY",
    )

    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

AYARLAR = Ayarlar()

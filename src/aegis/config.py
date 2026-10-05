from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_url: str = "sqlite:///aegis.db"
    dataset_path: Path = Path("aegis-dataset")
    llm_api_key: str | None = None

    model_config = SettingsConfigDict(env_prefix="AEGIS_", env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

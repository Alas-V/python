from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

TOKEN = "8205935139:AAGbVZYlX_feEfkvCsH-jIAJxPZDmZmYgsk"
PAYMENT_TOKEN = "1744374395:TEST:8e393a88736f9a72157a"


ADMIN_ID = 717149416


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def async_database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.DB_USER,
            password=self.DB_PASS,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )

    @property
    def sync_database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.DB_USER,
            password=self.DB_PASS,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )


settings = Settings()

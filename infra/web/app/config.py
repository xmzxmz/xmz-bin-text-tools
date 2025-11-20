"""Configuration settings for the web application."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    app_title: str = "BinTextTools"
    app_description: str = "Tools for Binary and Text data conversion via Web API"
    app_version: str = "0.2.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_prefix = "BINTEXT_"
        case_sensitive = False


settings = Settings()

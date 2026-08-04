from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    api_key: str = "changeme"
    database_url: str = "sqlite:///./app.db"
    rate_limit: str = "10/minute"
    cache_ttl_seconds: int = 300
    request_timeout_seconds: int = 30
    openai_model: str = "gpt-4o-mini"
    environment: str = "development"
    use_mock_llm: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

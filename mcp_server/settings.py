from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    oic_base_url: str = Field(..., alias="OIC_BASE_URL")
    oauth_token_url: str = Field(..., alias="OAUTH_TOKEN_URL")
    oauth_client_id: str = Field(..., alias="OAUTH_CLIENT_ID")
    oauth_client_secret: str = Field(..., alias="OAUTH_CLIENT_SECRET")
    oauth_scope: str | None = Field(None, alias="OAUTH_SCOPE")

    http_timeout_secs: int = Field(30, alias="HTTP_TIMEOUT_SECS")
    http_max_retries: int = Field(2, alias="HTTP_MAX_RETRIES")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 
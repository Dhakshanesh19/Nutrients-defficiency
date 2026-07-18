import json
from typing import List, Union
from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

def parse_cors(v: Union[str, List[str]]) -> List[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        if isinstance(v, str):
            return json.loads(v)
        return v
    raise ValueError(v)

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Nutrition Deficiency Predictor API"
    
    # JWT Security settings
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database configuration
    DATABASE_URL: str
    
    # CORS setup
    BACKEND_CORS_ORIGINS: Annotated[
        List[str],
        BeforeValidator(parse_cors)
    ] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()

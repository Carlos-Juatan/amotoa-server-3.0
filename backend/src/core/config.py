import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017/amotoa"
    PROJECT_NAME: str = "Amontoa Server Hub"
    API_V1_STR: str = "/api"
    MANGA_LN_SYNC_INTERVAL: int = 86400

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

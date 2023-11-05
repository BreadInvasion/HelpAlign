import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: str = ""
    pass_key: str = ""
    gmaps_key: str = ""


settings = Settings()
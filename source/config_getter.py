from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from pathlib import Path

def get_env_path():
    path = Path.cwd()
    while path.name != "TIH-tg-bot":
        path = path.parent
    path = path / "source" / ".env"
    return path

class Settings(BaseSettings):
    bot_token: SecretStr
    fernet_key: SecretStr
    model_config = SettingsConfigDict(env_file=get_env_path(), env_file_encoding='utf-8')

config = Settings()
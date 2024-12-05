from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    fernet_key: SecretStr
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

config = Settings()
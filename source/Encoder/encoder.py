from cryptography.fernet import Fernet
from source.config_getter import config

class Encoder:
    def __init__(self):
        self.__key = config.fernet_key.get_secret_value().encode('utf-8')
        self.__f = Fernet(self.__key)

    def encode_token(self, token: str) -> str:
        return self.__f.encrypt(token.encode('utf-8')).decode('utf-8')

    def decode_token(self, encoded_token: str) -> str:
        return self.__f.decrypt(encoded_token.encode('utf-8')).decode('utf-8')

token_encoder = Encoder()
from cryptography.fernet import Fernet
from config_getter import config

class Encoder:
    def __init__(self):
        self.__key = config.fernet_key.get_secret_value().encode('utf-8')
        self.__f = Fernet(self.__key)

    def encode_token(self, token: str) ->bytes:
        return self.__f.encrypt(token.encode('utf-8'))

    def decode_token(self, encoded_token: bytes) -> str:
        return self.__f.decrypt(encoded_token).decode('utf-8')

token_encoder = Encoder()
import unittest
from unittest_parametrize import parametrize, ParametrizedTestCase

from source.Bot.encoder import token_encoder

class TestEncoder(ParametrizedTestCase):
    @parametrize(
        "string",[
            ("ADIsn231$)@1",),
            ("31-`wf]aerwf",),
        ],
    )
    def test_encoding_and_decoding(self, string: str):
        self.assertEqual(token_encoder.decode_token(token_encoder.encode_token(string)), string)

if __name__ == '__main__':
    unittest.main()

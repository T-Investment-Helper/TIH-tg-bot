import unittest
import psycopg2
from source.Router.db_interaction import add_new_user, get_token_by_user_id
from source.config_getter import config

DB_SETTINGS = {
    "dbname": config.db_name.get_secret_value(),
    "user": config.db_username.get_secret_value(),
    "password": config.db_password.get_secret_value(),
    "host": config.db_host.get_secret_value(),
    "port": config.db_port.get_secret_value(),
    "sslmode": config.db_sslmode.get_secret_value()
}

class TestDatabaseFunctionsRealDB(unittest.TestCase):
    def setUp(self):
        self.connection = psycopg2.connect(**DB_SETTINGS)
        self.cursor = self.connection.cursor()

    def tearDown(self):
        self.cursor.close()
        self.connection.close()

    def test_add_new_user(self):
        user_id = 123
        token = "test_token"
        self.cursor.execute("DELETE FROM user_to_tokens WHERE user_id = %s;", (user_id,))
        self.connection.commit()
        add_new_user(user_id, token)
        self.cursor.execute("SELECT token FROM user_to_tokens WHERE user_id = %s;", (user_id,))
        result = self.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], token)

    def test_get_token_by_user_id_found(self):
        user_id = 456
        token = "found_test_token"
        self.cursor.execute("DELETE FROM user_to_tokens WHERE user_id = %s;", (user_id,))
        self.connection.commit()
        self.cursor.execute(
            "INSERT INTO user_to_tokens (user_id, token) VALUES (%s, %s);",
            (user_id, token)
        )
        self.connection.commit()
        result = get_token_by_user_id(user_id)
        self.assertEqual(result, token)

    def test_get_token_by_user_id_not_found(self):
        user_id = 789
        self.cursor.execute("DELETE FROM user_to_tokens WHERE user_id = %s;", (user_id,))
        self.connection.commit()
        result = get_token_by_user_id(user_id)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()

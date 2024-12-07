import psycopg2
import logging
from source.config_getter import config

logging.basicConfig(level=logging.INFO)

DB_SETTINGS = {
    "dbname": config.db_name.get_secret_value(),
    "user": config.db_username.get_secret_value(),
    "password": config.db_password.get_secret_value(),
    "host": config.db_host.get_secret_value(),
    "port": config.db_port.get_secret_value(),
    "sslmode": config.db_sslmode.get_secret_value()
}


def add_new_user(user_id, token):
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        cur = conn.cursor()
        insert_query = """
        INSERT INTO user_to_tokens (user_id, token)
        VALUES (%s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET token = EXCLUDED.token;
        """
        cur.execute(insert_query, (user_id, token))
        conn.commit()
        logging.info(f"Пользователь с ID '{user_id}' добавлен или обновлён.")
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Ошибка при добавлении пользователя: {e}")
        raise e


def get_token_by_user_id(user_id):
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        cur = conn.cursor()
        select_query = """
        SELECT token
        FROM user_to_tokens
        WHERE user_id = %s;
        """
        cur.execute(select_query, (user_id,))
        result = cur.fetchone()
        if result:
            token = result[0]
            logging.info(f"Получен токен для пользователя '{user_id}'")
            return token
        else:
            logging.warning(f"Пользователь с ID '{user_id}' не найден.")
            return None
    except Exception as e:
        logging.error(f"Ошибка при получении токена: {e}")
        return None
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

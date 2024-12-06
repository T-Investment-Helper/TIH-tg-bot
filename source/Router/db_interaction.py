import psycopg2
import logging

logging.basicConfig(level=logging.Info)

DB_SETTINGS = {
    "dbname": "railway",
    "user": "postgres",
    "password": "TxnpiXcklKwpRzFKakAVWlpODywHZoDB",
    "host": "junction.proxy.rlwy.net",
    "port": "44633",
    "sslmode": "require"
}

def add_new_user(user_id, token):
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        cur = conn.cursor()
        insert_query = """
        INSERT INTO user_to_tokens (user_id, token)
        VALUES (%s, %s);
        """
        cur.execute(insert_query, (user_id, token))
        conn.commit()
        logging.info(f"Пользователь с ID '{user_id}' добавлен.")
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Ошибка при добавлении пользователя: {e}")

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
            logging.info(f"Токен для пользователя '{user_id}': {token}")
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

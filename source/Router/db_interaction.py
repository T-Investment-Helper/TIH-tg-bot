import psycopg2

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
        print(f"Пользователь с ID '{user_id}' добавлен.")
        cur.close()
        conn.close()
    except Exception as e:
        print("Ошибка при добавлении пользователя:", str(e))

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
            print(f"Токен для пользователя '{user_id}': {token}")
            return token
        else:
            print(f"Пользователь с ID '{user_id}' не найден.")
            return None
    except Exception as e:
        print("Ошибка при получении токена:", str(e))
        return None
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

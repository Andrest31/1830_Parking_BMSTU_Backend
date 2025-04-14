import psycopg2

try:
    conn = psycopg2.connect(
        dbname='parking_db',
        user='parking_user',
        password='parking_pass',
        host='127.0.0.1',
        port='5432',
        options='-c client_encoding=utf8'
    )
    print("✅ Успешно подключено к базе данных!")
    conn.close()
except Exception as e:
    print("❌ Ошибка подключения:")
    print(e)

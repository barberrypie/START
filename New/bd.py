import psycopg2
from psycopg2 import Error
import os
from dotenv import load_dotenv
from pathlib import Path

connection = None

dotenv_path = Path(r'C:\\Projects\\New\\1.env')
load_dotenv(dotenv_path=dotenv_path)

try:
    connection = psycopg2.connect(user=os.getenv('BD_USER'),
                                  password=os.getenv('BD_PASS'),
                                  host=os.getenv('BD_HOST'),  
                                  port=os.getenv('BD_PORT'),
                                  database=os.getenv('BD_BD'))

    cursor = connection.cursor()
    cursor.execute("Delete from users where name = 'Сергей';")
    connection.commit()
    cursor.execute("SELECT * FROM users;")

    print("Команда успешно выполнена")

    records = cursor.fetchall()
    print('Результат:')
    for row in records:
        print(row)  

except (Exception, Error) as error:
    print("Ошибка при работе с PostgreSQL", error)
finally:
    if connection is not None:
        cursor.close()
        connection.close()
        print("Соединение с PostgreSQL закрыто")
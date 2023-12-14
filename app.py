from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from faker import Faker

app = Flask(__name__)

# Подключение к PostgreSQL
conn = psycopg2.connect(
    dbname='zbekinjp',
    user='zbekinjp',
    password='qSK2Bt5Pj-7stfPDTBBw79HmLNHzFbLL',
    host='berry.db.elephantsql.com',
    port=5432
)

# Создание курсора для взаимодействия с базой данных
cursor = conn.cursor()

# Создание экземпляра Faker
faker = Faker()

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Регистрация пользователя
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    # Вставка данных в таблицу users
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))

    # Сохранение изменений в базе данных
    conn.commit()

    return redirect(url_for('index'))

# Вход пользователя
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Проверка пользователя в базе данных
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()

    if user:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

# Отображение списка мероприятий
@app.route('/events')
def events_list():
    # Получение данных о мероприятиях из базы данных
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()

    return render_template('events.html', events=events)

# Создание мероприятия
@app.route('/create_event', methods=['POST'])
def create_event():
    event_name = request.form.get('event_name')
    event_date = request.form.get('event_date')

    # Вставка данных в таблицу events
    cursor.execute("INSERT INTO events (name, date) VALUES (%s, %s)", (event_name, event_date))

    # Сохранение изменений в базе данных
    conn.commit()

    return redirect(url_for('events_list'))

if __name__ == '__main__':
    app.run(debug=True)

# Закрытие курсора и соединения при завершении работы
cursor.close()
conn.close()



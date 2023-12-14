from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import psycopg2
from faker import Faker

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Замените на свой секретный ключ

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Конфигурация подключения к PostgreSQL
db_config = {
    "dbname": "volunteer_dv",
    "user": "postgres",
    "password": "Fudo2303",
    "host": "localhost",
    "port": 5432
}

# Подключение к PostgreSQL
conn = psycopg2.connect(**db_config)

# Создание курсора для взаимодействия с базой данных
cursor = conn.cursor()

# Создание экземпляра Faker
faker = Faker()

# Класс для представления пользователя
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# Заглушка для хранения пользователей (вместо использования БД для простоты)
users = {}

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Хеширование пароля перед сохранением в базу данных
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Вставка данных в таблицу users
        cursor.execute("""
            INSERT INTO users (username, password_hash, first_name, last_name, city, phone_number)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            username,
            hashed_password,
            faker.first_name(),
            faker.last_name(),
            faker.city(),
            faker.phone_number()
        ))

        # Сохранение изменений в базе данных
        conn.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Вход пользователя
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Проверка пользователя в базе данных
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user_data = cursor.fetchone()

    if user_data and bcrypt.check_password_hash(user_data[2], password):
        user = User(id=user_data[0], username=user_data[1])
        login_user(user)
        return redirect(url_for('index'))
    return redirect(url_for('login'))

# Выход пользователя
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Личный кабинет
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

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
    cursor.execute("""
        INSERT INTO events (name, date, description, organizer_id)
        VALUES (%s, %s, %s, %s)
    """, (
        event_name,
        event_date,
        faker.text(),
        current_user.id  # Организатор - текущий пользователь
    ))

    # Сохранение изменений в базе данных
    conn.commit()

    return redirect(url_for('events_list'))

# Закрытие курсора и соединения при завершении работы
cursor.close()
conn.close()

# Остальные маршруты
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import psycopg2
from faker import Faker
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField 
from wtforms.validators import InputRequired, ValidationError
from wtforms import DateField
from forms import RegistrationForm
from datetime import datetime


app = Flask(__name__)
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
    def __init__(self, id, username, role=None, additional_role=None):
        self.id = id
        self.username = username
        self.role = role
        self.additional_role = additional_role

@login_manager.user_loader
def load_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(id=user_data[0], username=user_data[1], role=user_data[6], additional_role=user_data[7])
    return None

# Заглушка для хранения пользователей (вместо использования БД для простоты)
users = {}

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

# Класс формы для создания ивента
# Внесите следующие изменения в класс EventForm
class EventForm(FlaskForm):
    event_name = StringField('Event Name', validators=[InputRequired()])
    event_date = DateField('Event Date', validators=[InputRequired()], format='%Y-%m-%d')
    role = SelectField('Role', choices=[('volunteer', 'Volunteer'), ('finder', 'Finder')], validators=[InputRequired()])
    availability = StringField('Availability', validators=[InputRequired()])  # Новое поле
    submit = SubmitField('Create Event')

    # Новое поле для указания свободных часов
    availability = StringField('Availability', validators=[InputRequired()])

    submit = SubmitField('Create Event')


# Класс формы для регистрации
class RegistrationFormCustom(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Register')

    def validate_username(self, field):
        cursor.execute("SELECT id FROM users WHERE username = %s", (field.data,))
        existing_user = cursor.fetchone()
        if existing_user:
            raise ValidationError('This username is already taken. Please choose a different one.')



# Отображение главной страницы
@app.route('/')
def index():
    return render_template('index.html')

# Отображение страницы "О нас"
@app.route('/about')
def about():
    return render_template('about.html')

# Отображение страницы "Контакты"
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Отображение страницы регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationFormCustom()

    if form.validate_on_submit():
        try:
            username = form.username.data
            password = form.password.data

            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('This username already exists. Please choose a different one.', 'danger')
                return render_template('register.html', form=form)

            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            # Используйте конкретные значения для роли и дополнительной роли
            role = 'volunteer'
            additional_role = None

            cursor.execute("""
                INSERT INTO users (username, password_hash, first_name, last_name, city, phone_number, role, additional_role)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                username,
                hashed_password,
                faker.first_name(),
                faker.last_name(),
                faker.city(),
                faker.phone_number(),
                role,
                additional_role
            ))

            conn.commit()

            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            new_user_data = cursor.fetchone()
            new_user = User(id=new_user_data[0], username=new_user_data[1])
            users[new_user.id] = new_user

            flash('Registration successful!', 'success')
            return redirect(url_for('login'))

        except psycopg2.Error as e:
            print(f"PostgreSQL error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')

    return render_template('register.html', form=form)


# # Удаление старой таблицы users (с учетом зависимостей)
# cursor.execute("DROP TABLE IF EXISTS users CASCADE")

# Создание новой таблицы users
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        city VARCHAR(255),
        phone_number VARCHAR(50),
        role VARCHAR(10) NOT NULL,
        additional_role VARCHAR(10)
    )
""")

# Создание новой таблицы events
cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        date DATE NOT NULL,
        description TEXT,
        organizer_id INTEGER REFERENCES users(id),
        role VARCHAR(20) NOT NULL,
        availability VARCHAR(255)  -- Добавленное поле для свободных часов
    )
""")


# Сохранение изменений в базе данных
conn.commit()

# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Проверка пользователя в базе данных
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()

        if user_data and bcrypt.check_password_hash(user_data[2], password):
            user = User(id=user_data[0], username=user_data[1])
            login_user(user)

            # Обновление заглушки users
            users[user.id] = user

            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

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
@app.route('/events', methods=['GET'])
def events_list():
    try:
        # Получение данных о мероприятиях из базы данных
        cursor.execute("SELECT * FROM events")
        events = cursor.fetchall()

        return render_template('events.html', events=events)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('error.html', error_message=str(e))

# Отображение мероприятий для волонтеров
@app.route('/events/volunteer', methods=['GET'])
@login_required
def volunteer_events():
    try:
        cursor.execute("SELECT * FROM events WHERE role = 'volunteer'")
        events = cursor.fetchall()
        return render_template('events.html', events=events)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('error.html', error_message=str(e))

# Отображение мероприятий для поисковиков
@app.route('/events/finder', methods=['GET'])
@login_required
def finder_events():
    try:
        cursor.execute("SELECT * FROM events WHERE role = 'finder'")
        events = cursor.fetchall()
        return render_template('events.html', events=events)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('error.html', error_message=str(e))



# Создание мероприятия
@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()

    if form.validate_on_submit():
        event_name = form.event_name.data
        event_date = form.event_date.data
        role = form.role.data
        availability = form.availability.data

        cursor.execute("""
            INSERT INTO events (name, date, description, organizer_id, role, availability)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            event_name,
            event_date,
            faker.text(),
            current_user.id,
            role,
            availability
        ))

        conn.commit()

        flash('Event created successfully!', 'success')
        return redirect(url_for('events_list'))

    return render_template('create_event.html', form=form)

# Обработчик ошибок
@app.errorhandler(405)
def handle_405_error(e):
    print(f"Error: {e}")
    return render_template('error.html', error_message="Method Not Allowed")

if __name__ == '__main__':
    app.secret_key = 'Fudo2303'
    app.run(debug=True)

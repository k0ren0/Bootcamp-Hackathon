from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
import psycopg2
from faker import Faker
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField 
from wtforms.validators import InputRequired, ValidationError
from wtforms import DateField
from flask_login import current_user


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

# @login_manager.user_loader
# def load_user(user_id):
#     return users.get(int(user_id))

# Класс формы для создания ивента
class EventForm(FlaskForm):
    event_name = StringField('Event Name', validators=[InputRequired()])
    event_date = DateField('Event Date', validators=[InputRequired()], format='%Y-%m-%d')
    role = SelectField('Role', choices=[('volunteer', 'Volunteer'), ('finder', 'Finder')], validators=[InputRequired()])
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
            role = 'user'
            additional_role = None

            # cursor.execute("""
            #     INSERT INTO users (username, first_name, last_name, city, phone_number, role, additional_role, password_hash)
            #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            # """, (
            #     username,
            #     faker.first_name(),
            #     faker.last_name(),
            #     faker.city(),
            #     faker.phone_number(),
            #     role,
            #     additional_role,
            #     hashed_password
            # ))

            cursor.execute("""
                INSERT INTO users (username, first_name, last_name, city, phone_number, role, additional_role, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                username,
                faker.first_name(),
                faker.last_name(),
                faker.city(),
                faker.phone_number(),
                'user',  # Роль по умолчанию
                None,    # Дополнительная роль по умолчанию
                hashed_password
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
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        city VARCHAR(255),
        phone_number VARCHAR(50),
        role VARCHAR(10) NOT NULL,
        additional_role VARCHAR(10),
        password_hash VARCHAR(255) NOT NULL
    )
""")

# Создание новой таблицы events
cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        date DATE NOT NULL,
        description TEXT,
        organizer_id INTEGER REFERENCES users(id),  -- Внешний ключ для связи с пользователем
        role VARCHAR(20) NOT NULL
    );
""")


# Создание новой таблицы event_participants
cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_participants (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),    -- Внешний ключ для связи с пользователем
        event_id INTEGER REFERENCES events(id)   -- Внешний ключ для связи с мероприятием
    );
""")



# Сохранение изменений в базе данных
conn.commit()

# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Проверка пользователя в базе данных
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()

        if user_data and bcrypt.check_password_hash(user_data[-1], password):
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
    try:
        # Получение данных о пользователе из базы данных
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user.id,))
        user_data = cursor.fetchone()

        if user_data:
            user = User(id=user_data[0], username=user_data[1], role=user_data[6], additional_role=user_data[7])

            # Добавим дополнительные данные из базы данных
            user.first_name = user_data[2]
            user.last_name = user_data[3]
            user.city = user_data[4]
            user.phone_number = user_data[5]

            # Получение мероприятий пользователя
            cursor.execute("SELECT * FROM events WHERE organizer_id = %s", (current_user.id,))
            user_events = cursor.fetchall()

            return render_template('profile.html', user=user, user_events=user_events)
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('index'))

    except Exception as e:
        print(f"Error: {e}")
        return render_template('error.html', error_message=str(e))

# @app.route('/events')
# def events():
#     return render_template('events.html')

# Отображение списка мероприятий
@app.route('/events', methods=['GET', 'POST'])
def events():
    try:
        if current_user.is_authenticated:
            form = EventForm()  # Создание формы внутри условия

            if request.method == 'POST' and form.validate_on_submit():
                # Обработка данных формы, если запрос типа POST
                event_name = form.event_name.data
                event_date = form.event_date.data
                role = form.role.data  # Получаем выбранную роль

                # Вставка данных в таблицу events
                cursor.execute("""
                    INSERT INTO events (name, date, description, organizer_id, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    event_name,
                    event_date,
                    faker.text(),  # Пример описания, замените на реальное описание
                    current_user.id,
                    role  # Используем выбранную роль
                ))

                # Получение идентификатора только что созданного мероприятия
                cursor.execute("SELECT lastval()")
                event_id = cursor.fetchone()[0]

                # Вставка данных в таблицу event_participants
                cursor.execute("""
                    INSERT INTO event_participants (user_id, event_id)
                    VALUES (%s, %s)
                """, (
                    current_user.id,
                    event_id
                ))

                # Сохранение изменений в базе данных
                conn.commit()

                flash(f'{role.capitalize()} Event created successfully!', 'success')
                return redirect(url_for('events'))

            # Получение данных о мероприятиях из базы данных в зависимости от роли пользователя
            if current_user.role == 'volunteer':
                cursor.execute("""
                    SELECT e.* FROM events e
                    JOIN event_participants ep ON e.id = ep.event_id
                    WHERE e.role = 'volunteer' AND ep.user_id = %s
                """, (current_user.id,))
            elif current_user.role == 'finder':
                cursor.execute("""
                    SELECT e.* FROM events e
                    JOIN event_participants ep ON e.id = ep.event_id
                    WHERE e.role = 'finder' AND ep.user_id = %s
                """, (current_user.id,))
            else:
                cursor.execute("SELECT * FROM events")
            events = cursor.fetchall()

            # Получение данных о мероприятиях для волонтеров
            cursor.execute("""
                SELECT e.* FROM events e
                JOIN event_participants ep ON e.id = ep.event_id
                WHERE e.role = 'volunteer' AND ep.user_id = %s
            """, (current_user.id,))
            volunteer_events = cursor.fetchall()

            # Получение данных о мероприятиях для поисковиков
            cursor.execute("""
                SELECT e.* FROM events e
                JOIN event_participants ep ON e.id = ep.event_id
                WHERE e.role = 'finder' AND ep.user_id = %s
            """, (current_user.id,))
            finder_events = cursor.fetchall()

            return render_template('events.html', events=events, volunteer_events=volunteer_events, finder_events=finder_events, form=form)
        else:
            flash('Please log in to view events.', 'info')
            return redirect(url_for('login'))
    except Exception as e:
        print(f"Error: {e}")
        return render_template('error.html', error_message=str(e))

# Класс формы для создания мероприятия волонтеров
class VolunteerEventForm(EventForm):
    # Можно добавить дополнительные поля, специфичные для мероприятий волонтеров
    pass

# Создание мероприятия для волонтеров
@app.route('/volunteer_events', methods=['GET', 'POST'])
@login_required
def volunteer_events():
    form = VolunteerEventForm()  # Используем VolunteerEventForm

    if form.validate_on_submit():
        event_name = form.event_name.data
        event_date = form.event_date.data
        role = form.role.data  # Получаем выбранную роль

        # Вставка данных в таблицу events
        cursor.execute("""
            INSERT INTO events (name, date, description, organizer_id, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            event_name,
            event_date,
            faker.text(),  # Пример описания, замените на реальное описание
            current_user.id,
            role  # Используем выбранную роль
        ))

        # Получение идентификатора только что созданного мероприятия
        cursor.execute("SELECT lastval()")
        event_id = cursor.fetchone()[0]

        # Вставка данных в таблицу event_participants
        cursor.execute("""
            INSERT INTO event_participants (user_id, event_id)
            VALUES (%s, %s)
        """, (
            current_user.id,
            event_id
        ))

        # Сохранение изменений в базе данных
        conn.commit()

        flash(f'{role.capitalize()} Event created successfully!', 'success')
        return redirect(url_for('events'))

    return render_template('volunteer_events.html', form=form)

# Класс формы для создания мероприятия поисковиков
class FinderEventForm(EventForm):
    # Можно добавить дополнительные поля, специфичные для мероприятий поисковиков
    pass

# Создание мероприятия для поисковиков
@app.route('/finder_events', methods=['GET', 'POST'])
@login_required
def finder_events():
    form = FinderEventForm()  # Используем FinderEventForm

    if form.validate_on_submit():
        event_name = form.event_name.data
        event_date = form.event_date.data

        # Вставка данных в таблицу events
        cursor.execute("""
            INSERT INTO events (name, date, description, organizer_id, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            event_name,
            event_date,
            faker.text(),  # Пример описания, замените на реальное описание
            current_user.id,
            'finder'  # Указываем роль поисковика
        ))

        # Получение идентификатора только что созданного мероприятия
        cursor.execute("SELECT lastval()")
        event_id = cursor.fetchone()[0]

        # Вставка данных в таблицу event_participants
        cursor.execute("""
            INSERT INTO event_participants (user_id, event_id)
            VALUES (%s, %s)
        """, (
            current_user.id,
            event_id
        ))

        # Сохранение изменений в базе данных
        conn.commit()

        flash('Finder Event created successfully!', 'success')
        return redirect(url_for('events'))

    return render_template('finder_events.html', form=form)

# Обработчик ошибок
@app.errorhandler(405)
def handle_405_error(e):
    print(f"Error: {e}")
    return render_template('error.html', error_message="Method Not Allowed")

if __name__ == '__main__':
    app.secret_key = 'Fudo2303'
    app.run(debug=True)

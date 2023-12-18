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

# PostgreSQL connection configuration
db_config = {
    "dbname": "volunteer_dv",
    "user": "postgres",
    "password": "Fudo2303",
    "host": "localhost",
    "port": 5432
}

# Connecting to PostgreSQL
conn = psycopg2.connect(**db_config)

# Creating a cursor for interacting with the database
cursor = conn.cursor()

# Creating an instance of Faker
faker = Faker()

# Class to represent a user
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

# Placeholder for storing users (instead of using a database for simplicity)
users = {}

# Form class for creating an event
class EventForm(FlaskForm):
    event_name = StringField('Event Name', validators=[InputRequired()])
    event_date = DateField('Event Date', validators=[InputRequired()], format='%Y-%m-%d')
    role = SelectField('Role', choices=[('volunteer', 'Volunteer'), ('finder', 'Finder')], validators=[InputRequired()])
    submit = SubmitField('Create Event')

# Registration form class
class RegistrationFormCustom(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Register')

    def validate_username(self, field):
        cursor.execute("SELECT id FROM users WHERE username = %s", (field.data,))
        existing_user = cursor.fetchone()
        if existing_user:
            raise ValidationError('This username is already taken. Please choose a different one.')

# Displaying the main page
@app.route('/')
def index():
    return render_template('index.html')

# Displaying the "About Us" page
@app.route('/about')
def about():
    return render_template('about.html')

# Displaying the "Contact" page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Displaying the registration page
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

            # Use specific values for role and additional role
            role = 'user'
            additional_role = None

            cursor.execute("""
                INSERT INTO users (username, first_name, last_name, city, phone_number, role, additional_role, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                username,
                faker.first_name(),
                faker.last_name(),
                faker.city(),
                faker.phone_number(),
                role,
                additional_role,
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

# Creating a new users table
cursor.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(255) NOT NULL, first_name VARCHAR(255), last_name VARCHAR(255), city VARCHAR(255), phone_number VARCHAR(50), role VARCHAR(10) NOT NULL, additional_role VARCHAR(10), password_hash VARCHAR(255) NOT NULL)")

# Creating a new events table
cursor.execute("CREATE TABLE IF NOT EXISTS events (id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL, date DATE NOT NULL, description TEXT, organizer_id INTEGER REFERENCES users(id), role VARCHAR(20) NOT NULL)")

# Creating a new event_participants table
cursor.execute("CREATE TABLE IF NOT EXISTS event_participants (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id), event_id INTEGER REFERENCES events(id))")

# Saving changes to the database
conn.commit()

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Checking the user in the database
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()

        if user_data and bcrypt.check_password_hash(user_data[-1], password):
            user = User(id=user_data[0], username=user_data[1])
            login_user(user)

            # Updating the users placeholder
            users[user.id] = user

            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

# User logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# User profile
@app.route('/profile')
@login_required
def profile():
    try:
        # Getting user data from the database
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user.id,))
        user_data = cursor.fetchone()

        if user_data:
            user = User(id=user_data[0], username=user_data[1], role=user_data[6], additional_role=user_data[7])

            # Adding additional data from the database
            user.first_name = user_data[2]
            user.last_name = user_data[3]
            user.city = user_data[4]
            user.phone_number = user_data[5]

            # Getting user events
            cursor.execute("SELECT * FROM events WHERE organizer_id = %s", (current_user.id,))
            user_events = cursor.fetchall()

            return render_template('profile.html', user=user, user_events=user_events)
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('index'))

    except Exception as e:
        print(f"Error: {e}")
        return render_template('error.html', error_message=str(e))

# Displaying the list of events
@app.route('/events', methods=['GET', 'POST'])
def events():
    try:
        if current_user.is_authenticated:
            form = EventForm()  # Creating the form inside the condition

            if request.method == 'POST' and form.validate_on_submit():
                # Handling form data if the request type is POST
                event_name = form.event_name.data
                event_date = form.event_date.data
                role = form.role.data  # Getting the selected role

                # Inserting data into the events table
                cursor.execute("""
                    INSERT INTO events (name, date, description, organizer_id, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    event_name,
                    event_date,
                    faker.text(),  # Example description, replace with a real description
                    current_user.id,
                    role  # Using the selected role
                ))

                # Getting the ID of the newly created event
                cursor.execute("SELECT lastval()")
                event_id = cursor.fetchone()[0]

                # Inserting data into the event_participants table
                cursor.execute("""
                    INSERT INTO event_participants (user_id, event_id)
                    VALUES (%s, %s)
                """, (
                    current_user.id,
                    event_id
                ))

                # Saving changes to the database
                conn.commit()

                flash(f'{role.capitalize()} Event created successfully!', 'success')
                return redirect(url_for('events'))

            # Getting data about events from the database depending on the user's role
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

            # Getting data about events for volunteers
            cursor.execute("""
                SELECT e.* FROM events e
                JOIN event_participants ep ON e.id = ep.event_id
                WHERE e.role = 'volunteer' AND ep.user_id = %s
            """, (current_user.id,))
            volunteer_events = cursor.fetchall()

            # Getting data about events for finders
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

# Form class for creating volunteer events
class VolunteerEventForm(EventForm):
    # Additional fields specific to volunteer events can be added here
    pass

# Creating a volunteer event
@app.route('/volunteer_events', methods=['GET', 'POST'])
@login_required
def volunteer_events():
    form = VolunteerEventForm()  # Using VolunteerEventForm

    if form.validate_on_submit():
        event_name = form.event_name.data
        event_date = form.event_date.data
        role = form.role.data  # Getting the selected role

        # Inserting data into the events table
        cursor.execute("""
            INSERT INTO events (name, date, description, organizer_id, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            event_name,
            event_date,
            faker.text(),  # Example description, replace with a real description
            current_user.id,
            role  # Using the selected role
        ))

        # Getting the ID of the newly created event
        cursor.execute("SELECT lastval()")
        event_id = cursor.fetchone()[0]

        # Inserting data into the event_participants table
        cursor.execute("""
            INSERT INTO event_participants (user_id, event_id)
            VALUES (%s, %s)
        """, (
            current_user.id,
            event_id
        ))

        # Saving changes to the database
        conn.commit()

        flash(f'{role.capitalize()} Event created successfully!', 'success')
        return redirect(url_for('events'))

    return render_template('volunteer_events.html', form=form)

# Form class for creating finder events
class FinderEventForm(EventForm):
    # Additional fields specific to finder events can be added here
    pass

# Creating a finder event
@app.route('/finder_events', methods=['GET', 'POST'])
@login_required
def finder_events():
    form = FinderEventForm()  # Using FinderEventForm

    if form.validate_on_submit():
        event_name = form.event_name.data
        event_date = form.event_date.data

        # Inserting data into the events table
        cursor.execute("""
            INSERT INTO events (name, date, description, organizer_id, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            event_name,
            event_date,
            faker.text(),  # Example description, replace with a real description
            current_user.id,
            'finder'  # Specifying the finder role
        ))

        # Getting the ID of the newly created event
        cursor.execute("SELECT lastval()")
        event_id = cursor.fetchone()[0]

        # Inserting data into the event_participants table
        cursor.execute("""
            INSERT INTO event_participants (user_id, event_id)
            VALUES (%s, %s)
        """, (
            current_user.id,
            event_id
        ))

        # Saving changes to the database
        conn.commit()

        flash('Finder Event created successfully!', 'success')
        return redirect(url_for('events'))

    return render_template('finder_events.html', form=form)

# Error handler
@app.errorhandler(405)
def handle_405_error(e):
    print(f"Error: {e}")
    return render_template('error.html', error_message="Method Not Allowed")

if __name__ == '__main__':
    app.secret_key = 'Fudo2303'
    app.run(debug=True)

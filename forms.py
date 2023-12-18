from wtforms import StringField, DateField, SelectField, SubmitField
from wtforms.validators import InputRequired
from flask_wtf import FlaskForm

class VolunteerEventForm(FlaskForm):
    event_name = StringField('Event Name', validators=[InputRequired()])
    event_date = DateField('Event Date', validators=[InputRequired()], format='%Y-%m-%d')
    role = SelectField('Role', choices=[('volunteer', 'Volunteer'), ('finder', 'Finder')], validators=[InputRequired()])
    submit = SubmitField('Create Event')

class FinderEventForm(FlaskForm):
    # Add FinderEventForm fields if needed
    pass
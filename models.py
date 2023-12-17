from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, first_name, last_name, city, phone_number, role=None, additional_role=None, organized_events=None):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.city = city
        self.phone_number = phone_number
        self.role = role
        self.additional_role = additional_role
        self.organized_events = organized_events if organized_events is not None else []


# @login_manager.user_loader
# def load_user(user_id):
#     cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
#     user_data = cursor.fetchone()
#     if user_data:
#         return User(id=user_data[0], username=user_data[1], password_hash=user_data[2],
#                     first_name=user_data[3], last_name=user_data[4], city=user_data[5],
#                     phone_number=user_data[6], role=user_data[7], additional_role=user_data[8])
#     return None

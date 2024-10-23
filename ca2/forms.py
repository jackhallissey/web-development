from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField
from wtforms.validators import InputRequired, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField("Username",
                            validators=[InputRequired()])
    password = PasswordField("Password",
                            validators=[InputRequired()])
    password2 = PasswordField("Confirm Password",
                            validators=[InputRequired(), EqualTo("password", "Passwords must match.")])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")

class AddResultsForm(FlaskForm):
    choice = RadioField(choices=["Yes", "No"], default="Yes")
    submit = SubmitField("Continue")
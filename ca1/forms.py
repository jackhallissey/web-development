from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, PasswordField, BooleanField, DateField, DecimalField, RadioField, IntegerField
from wtforms.validators import InputRequired, EqualTo, Optional, NumberRange

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

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Current Password",
                            validators=[InputRequired()])
    new_password = PasswordField("New Password",
                            validators=[InputRequired()])
    new_password2 = PasswordField("Confirm New Password",
                            validators=[InputRequired(), EqualTo("new_password", "Passwords must match.")])
    submit = SubmitField("Submit")

class ConfirmationForm1(FlaskForm):
    check = BooleanField("I understand that this cannot be undone.",
                            validators=[InputRequired()])
    submit = SubmitField("Confirm")

class ConfirmationForm2(FlaskForm):
    submit = SubmitField("Confirm")

class RatingForm(FlaskForm):
    score = SelectField("Score",
                           choices=[n for n in range(1, 11)])
    review = StringField("Review (optional)")
    submit = SubmitField("Submit")

class ListSettingsForm(FlaskForm):
    name = StringField("Name", validators=[InputRequired()])
    visibility = SelectField("Visibility", choices=[(1, "Public"), (0, "Private")])
    submit = SubmitField("Save")

class ListRemoveForm(FlaskForm):
    movie = SelectField(choices=[], validators=[InputRequired()])
    submit = SubmitField("Submit")

class ListAddForm(FlaskForm):
    list = SelectField(choices=[], validators=[InputRequired()])
    submit = SubmitField("Submit")

class SearchForm(FlaskForm):
    query = StringField()
    submit = SubmitField("Search")

class AdvancedSearchForm(FlaskForm):
    search_term = StringField("Search Term")
    min_date = DateField("Released After", validators=[Optional()])
    max_date = DateField("Released Before", validators=[Optional()])
    min_score = DecimalField("Minimum Score", validators=[Optional(), NumberRange(0, 10)])
    max_score = DecimalField("Maximum Score", validators=[Optional(), NumberRange(0, 10)])
    genre = SelectField("Genre", choices=[("", "All")], default="")
    sort1 = SelectField("Primary Sort", choices=[("title", "Title"), ("avg_score", "Score"), ("date", "Release Date"), ("runtime", "Runtime")], default="title")
    sort1_order = RadioField(choices=["Ascending", "Descending"], default="Ascending")
    sort2 = SelectField("Secondary Sort", choices=[("", ""), ("title", "Title"), ("avg_score", "Score"), ("date", "Release Date"), ("runtime", "Runtime")], default="")
    sort2_order = RadioField(choices=["Ascending", "Descending"], default="Ascending")
    submit = SubmitField("Search")

class MovieInfoForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    synopsis = StringField("Synopsis", validators=[InputRequired()])
    date = DateField("Release Date", validators=[InputRequired()])
    runtime = IntegerField("Runtime", validators=[InputRequired()])
    poster = SelectField("Poster", validators=[InputRequired()], default="default.jpg")
    poster_src = StringField("Attribution for Poster")
    submit = SubmitField("Submit")

class GenreForm(FlaskForm):
    name = StringField("Genre Name", validators=[InputRequired()])
    submit = SubmitField("Submit")

class DeleteGenreForm(FlaskForm):
    genre = SelectField("Genre", choices=[])
    check = BooleanField("I understand that this cannot be undone.",
                            validators=[InputRequired()])
    submit = SubmitField("Submit")

class AssignGenresForm(FlaskForm):
    genre1 = SelectField("Genre 1", choices=[])
    genre2 = SelectField("Genre 2", choices=[])
    genre3 = SelectField("Genre 3", choices=[])
    submit = SubmitField("Submit")
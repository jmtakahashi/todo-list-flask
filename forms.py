from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField

from wtforms.validators import DataRequired, Email, Length


class TodoAddForm(FlaskForm):
    """Form for adding todos."""

    todo = StringField('New Todo', validators=[DataRequired()])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6)])


class UserAddForm(FlaskForm):
    """User add form."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6)])

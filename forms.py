from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField, BooleanField, SelectField, DateField, RadioField

from wtforms.validators import DataRequired, Email, Length, Optional
import email_validator


class TodoAddForm(FlaskForm):
    """Form for adding todos."""

    todo = StringField('New Todo', validators=[DataRequired()])
    # done = HiddenField('Done?', default=False, validators=[
    #     DataRequired()])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6)])


class UserAddForm(FlaskForm):
    """User add form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6)])

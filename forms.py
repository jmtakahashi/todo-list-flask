from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField

from wtforms.validators import DataRequired, Email, Length


class TodoAddForm(FlaskForm):
    """Form for adding todos."""

    todo = StringField('New Todo', validators=[
                       DataRequired("Please enter a todo!")])


class LoginForm(FlaskForm):
    """Login form."""

    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6)])


class UserAddForm(FlaskForm):
    """User add form."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6)])


class UserEditForm(FlaskForm):
    """User edit form."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    newPassword = PasswordField('Password', validators=[
        DataRequired(), Length(min=6)])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=6)])


class UserDeleteForm(FlaskForm):
    """User delete form."""

    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=6)])

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField

from wtforms.validators import DataRequired, Email, Length


class TodoAddForm(FlaskForm):
    """Form for adding todos."""

    todo = StringField('New Todo', render_kw={"placeholder": "New todo"}, validators=[
                       DataRequired("Please enter a todo.")])


class LoginForm(FlaskForm):
    """Login form."""

    email = EmailField('Email', validators=[
                       DataRequired('Please enter your email.'), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired('Please enter your password.'), Length(min=6)])


class UserAddForm(FlaskForm):
    """User add form."""

    username = StringField('Username', validators=[DataRequired(
        'Please enter a username.  This can be changed later.')])
    email = StringField('Email', validators=[DataRequired(
        'Please enter a password.  This can be changed later.'), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6)])


class UserEditForm(FlaskForm):
    """User edit form."""

    username = StringField('Username', validators=[
                           DataRequired('Username cannot be blank.')])
    email = StringField('Email', validators=[
                        DataRequired('Email cannot be blank.'), Email()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=6)])
    password = PasswordField('Password', validators=[
        DataRequired('Please enter your password to make changes.'), Length(min=6)])


class UserDeleteForm(FlaskForm):
    """User delete form."""

    password = PasswordField('Password', validators=[
        DataRequired('Account deletion requires your password.'), Length(min=6)])

import os

# from termcolor import colored

from flask import Flask, render_template, request, redirect, flash, jsonify, session, g
from sqlalchemy.exc import IntegrityError

# import text so we can use fstrings in our filter/sort queries
from sqlalchemy.sql import text

from flask_debugtoolbar import DebugToolbarExtension
from flask_cors import CORS

from forms import TodoAddForm, LoginForm, UserAddForm
from models import db, connect_db, Todo, User


app = Flask(__name__)
cors = CORS(app)

# below line necessary to run seed.py (https://stackoverflow.com/a/74364913/7207125)
# app.app_context().push()

###############################################################################
# config

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
if os.environ.get("FLASK_ENV") == "devlopment":
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///todo_list'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.environ.get('DATABASE_URL', 'postgresql:///todo_list'))

# sqlalchemy
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

# debug toolbar
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# wtforms secrect key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")

# address warning in the browser console
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#samesitesamesite-value
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = 'True'

toolbar = DebugToolbarExtension(app)


###############################################################################
# connect to the db (this function imported from models.py)

connect_db(app)


###############################################################################
# set the name of the key we will use on the session obj -> "curr_user"
# so session[CURR_USER_KEY] = session["curr_user"]

CURR_USER_KEY = "curr_user"


###############################################################################
# do this before every request!

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    # if there is session["curr_user"] exists then add it to our Flask "g" global
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


###############################################################################
# login, logout, signup

def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    # on logout, if session["curr_user"] exists, del from session
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Display signup form and Handle user signup."""

    form = UserAddForm()

    if form.validate_on_submit():
        u = User.signup(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
        )

        try:
            db.session.add(u)
            db.session.commit()

        except IntegrityError as exc:
            flash("Account exists please login!", 'danger')
            return redirect('/')

        do_login(u)

        # after we do_login() we redirect to index again, but add_user_to_g() will
        # run and we will have g.user when we redirect to the index page.
        return redirect('/todos')

    # if form not validated just display the template
    return render_template('signup.html', form=form)


@app.route('/logout', methods=["GET"])
def logout():
    """Logout from app."""

    do_logout()

    return redirect("/")


###############################################################################
# homepage - login

@app.route("/", methods=["GET", "POST"])
def home_page():
    """The home page.  Authenticate user and redirect to todos page."""

    form = LoginForm()

    if form.validate_on_submit():
        u = User.authenticate(form.email.data,
                              form.password.data)

        # is u comes back with data, login our user.
        # if u comes back with False, set a flash message
        if u:
            do_login(u)

        else:
            flash("Invalid login credentials.  Please try again.", 'danger')
            return redirect("/")

        # if no errors thrown, send user to /todos with a success msg
        flash("Login successful!", "success")
        return redirect("/todos")

    return render_template('index.html', form=form)


###############################################################################
# todos - show todos + add todo - requires auth

@app.route('/todos', methods=['GET', 'POST'])
def show_todos():
    """Show all todos, with the add todo form."""

    if not g.user:
        flash("Please login!", "danger")
        return redirect("/")

    form = TodoAddForm()

    if form.validate_on_submit():
        new_todo = Todo(todo=form.todo.data)

        try:
            db.session.add(new_todo)
            db.session.commit()

        except IntegrityError as exc:
            flash("Please try adding the todo again.", "danger")

        flash("Todo added!", "success")
        return redirect("/todos")

    # initialize a var so we can pass it to the template (python scope issue)
    todos = []

    # this is additional security to ensure no todos are passed w/o logging in.
    # if we don't check that user is logged in first and simply got all todos,
    # we wouldn't see them on the front-end because we also check using jinja
    # but the todos arg would still be passed to the index.html view.
    # this stops Flask from sending any todos if no user is logged in.
    if CURR_USER_KEY in session:
        todos = Todo.query.all()

    print("")
    print("****************")
    print(todos)
    print("****************")
    print("")

    return render_template('todos.html', form=form, todos=todos)

import os
import json

from termcolor import colored

from flask import Flask, render_template, request, redirect, flash, jsonify
from flask import session, g
from sqlalchemy.exc import IntegrityError

# import text so we can use fstrings in our filter/sort queries
from sqlalchemy.sql import text


from flask_debugtoolbar import DebugToolbarExtension
from flask_cors import CORS

from forms import TodoAddForm, LoginForm, UserAddForm

from models import db, connect_db, Todo, User


cors = CORS()
app = Flask(__name__)

# blow line necessary to run (https://stackoverflow.com/a/74364913/7207125)
app.app_context().push()

###############################################################################
# config

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///todo_list'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
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

    session[CURR_USER_KEY] = user.username


def do_logout():
    """Logout user."""

    # on logout, if session["curr_user"] exists, del from session
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to /home with new user logged in.

    If form not valid, present form.

    If the there already is a user with that username: flash message and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            # send our user info to be registered
            u = User.signup(
                username=form.username.data,
                password=form.password.data,

            )

            # if there's an error in the above method, the except will be thrown

            # commit our added user
            db.session.commit()

            # after db.session.commit() the user will contain the id from our db
            do_login(u)

        except IntegrityError as exc:

            flash("Username already exists!", 'danger')
            return render_template('/signup.html', form=form)

        return redirect('/')

    return render_template('signup.html', form=form)


###############################################################################
# index route login, todos/addTodo

@app.route("/", methods=["GET", "POST"])
def home_page():
    """The home page.  If user is not logged in, show login form."""

    login_form = LoginForm()
    todo_form = TodoAddForm()

    # validatiion for our login_form
    if login_form.validate_on_submit():
        try:
            # attempt authentication
            u = User.authenticate(login_form.username.data,
                                  login_form.password.data)

            if u:
                # login our user
                do_login(u)

            return redirect("/")

        except IntegrityError as exc:

            flash("Try again...", 'danger')
            return redirect("/")

    # validatiion for our todo_form
    if todo_form.validate_on_submit():
        try:
            # attempt add our todo
            todo = Todo.add_todo(todo_form.todo.data)

            if todo:
                # commit our added todo
                db.session.commit()

            return redirect("/")

        except IntegrityError as exc:

            flash("Please try adding the todo again.", "danger")
            return redirect("/")

    # if user is logged in, get all our todos and pass to index.html
    todos = {}

    if CURR_USER_KEY in session:
        todos = Todo.query.all()

    return render_template('index.html', login_form=login_form, todo_form=todo_form, todos=todos)


###############################################################################
# api routes - todos

# get todos
@app.route("/api/todos", methods=["GET"])
def get_todos():
    """Get all todos."""

    todos = Todo.query.all()

    # if no todos found, respond with message
    if len(todos) == 0:
        resp = jsonify(message="no todos found")
        return (resp)

    data = [todo.serialize() for todo in todos]
    resp = jsonify(todos=data)
    return (resp)


# add a todo
@ app.route("/api/todos", methods=["POST"])
def add_todo():
    """Add a todo. Returns the newly added todo."""

    # attempt to get our data from the post request
    data = request.json.get("todo")

    # if the data we need is not in the request, throw an error
    if not data:
        resp = jsonify(message="Missing required data")
        return (resp, 400)

    # if data is there, try to add to the db
    try:
        new_todo = Todo(todo=data)

        db.session.add(new_todo)

        db.session.commit()

        data = new_todo.serialize()
        resp = jsonify(todo=data)
        return (resp, 201)

    except:
        resp = jsonify(message="Todo not created")
        return (resp, 400)


# get a single todo
@ app.route("/api/todos/<int:id>", methods=["GET"])
def get_todo(id):
    """Get a single todo by id."""

    try:
        result = Todo.query.get_or_404(id)

        data = result.serialize()

        resp = jsonify(todo=data)
        return (resp)

    except:
        resp = jsonify(message="todo not found")
        return (resp, 404)


# edit a todo
@ app.route("/api/todos/<int:id>", methods=["PATCH"])
def edit_todo(id):
    """Edit a single todo by id. Returns the edited todo."""

    try:
        # get our
        todo = Todo.query.get_or_404(id)

        # update our todo with new data
        todo.todo = request.json.get("todo", todo.todo)
        todo.done = request.json.get("done", todo.done)

        db.session.commit()

        data = todo.serialize()

        resp = jsonify(todo=data)
        return (resp, 201)

    except:
        resp = jsonify(message="an error occured")
        return (resp, 404)


# delete a todo route #
@ app.route("/api/todos/<id>", methods=["DELETE"])
def delete_todo(id):
    """Delete a single todo by id."""

    try:
        # below we delete the item in sqlalchemy, but we need db.session.commit()
        todo = Todo.query.get_or_404(id)

        db.session.delete(todo)

        db.session.commit()

        resp = jsonify(deleted=id)
        return (resp)

    except:
        resp = jsonify(message="an error occured")
        return (resp, 404)


###############################################################################
# api routes - users

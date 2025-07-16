import os
from datetime import datetime

# from termcolor import colored

from flask import Flask, render_template, request, redirect, flash, jsonify, session, g
from sqlalchemy.exc import IntegrityError

from flask_debugtoolbar import DebugToolbarExtension
from flask_cors import CORS

from forms import TodoAddForm, LoginForm, UserAddForm
from models import db, connect_db, Todo, User


app = Flask(__name__)
cors = CORS()


# below line necessary to run seed.py (https://stackoverflow.com/a/74364913/7207125)
# app.app_context().push()

###############################################################################
# config

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
if os.environ.get('FLASK_ENV') == "development":
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.environ.get('DATABASE_URL', 'postgresql:///todo_list'))
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.environ.get('SUPABASE_DATABASE_URL'))

# sqlalchemy
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

# debug toolbar
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# wtforms secrect key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")

# address warning in the browser console
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#samesitesamesite-value
# app.config['SESSION_COOKIE_SAMESITE'] = 'None'
# app.config['SESSION_COOKIE_SECURE'] = 'True'

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
            flash("Account exists please login!", 'error')
            return redirect('/')

        do_login(u)

        return redirect('/todos')

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

    if CURR_USER_KEY in session:
        return redirect("/todos")

    form = LoginForm()

    if form.validate_on_submit():
        u = User.authenticate(form.email.data,
                              form.password.data)

        if u:
            do_login(u)

        else:
            flash("Invalid login credentials.  Please try again.", 'error')
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

    if CURR_USER_KEY not in session:
        flash("Please login!", "danger")
        return redirect("/")

    form = TodoAddForm()

    if form.validate_on_submit():
        new_todo = Todo(user_id=g.user.id, todo=form.todo.data)

        try:
            db.session.add(new_todo)
            db.session.commit()

        except IntegrityError as exc:
            flash("Please try adding the todo again.", "error")

        flash("Todo added!", "success")
        return redirect("/todos")

    # initialize a var so we can pass it to the template (python scope issue)
    todos = []

    if CURR_USER_KEY in session:
        t = Todo.query.order_by("id").all()
        # format datetime obj
        if len(t) > 0:
            for todo in t:
                formattedDate = todo.date_added.date().strftime("%m-%d-%Y")
                todo.date_added = formattedDate
                todos.append(todo)

    return render_template('todos.html', form=form, todos=todos)


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
    return (resp, 200)


# add a todo
@app.route("/api/todos", methods=["POST"])
def add_todo():
    """Add a todo. Returns the newly added todo."""

    # attempt to get our data from the post request
    data = request.json.get("todo")

    # if the data we need is not in the request, throw an error
    if not data:
        resp = jsonify(message="missing required data")
        return (resp, 400)

    # if data is there, try to add to the db
    new_todo = Todo(todo=data)

    try:
        db.session.add(new_todo)
        db.session.commit()

    except:
        resp = jsonify(message="todo not created")
        return (resp, 400)

    # serialize the todo (which now contains "id" and "complete" status),
    # create our resp and return
    data = new_todo.serialize()
    resp = jsonify(todo=data)
    return (resp, 201)


# get a single todo
@app.route("/api/todos/<int:id>", methods=["GET"])
def get_todo(id):
    """Get a single todo by id."""

    # get our todo.  if not found, the except block will run
    todo = Todo.query.get(id)

    if todo:
        # serialize the todo, create our resp and return
        data = todo.serialize()
        resp = jsonify(todo=data)
        return (resp)
    else:
        resp = jsonify(message="todo not found")
        return (resp, 404)


# edit a todo
@app.route("/api/todos/<int:id>", methods=["PATCH"])
def edit_todo(id):
    """Edit a single todo by id. Returns the edited todo."""

    # get our todo.  if not found, the except block will run
    todo = Todo.query.get(id)

    if todo:
        # update our todo with new data, giving default options if the data
        # doesn't exist in the json of the request
        todo.todo = request.json.get("todo", todo.todo)
        todo.complete = request.json.get("complete", todo.complete)

        try:
            db.session.commit()

        except:
            resp = jsonify(message="an error occured")
            return (resp, 400)

    else:
        resp = jsonify(message="todo not found")
        return (resp, 404)

    # serialize the todo, create our resp and return
    data = todo.serialize()
    resp = jsonify(todo=data)
    return (resp, 200)


# delete a todo route
@app.route("/api/todos/<id>", methods=["DELETE"])
def delete_todo(id):
    """Delete a single todo by id."""

    todo = Todo.query.get(id)

    if todo:
        try:
            db.session.delete(todo)
            db.session.commit()

        except:
            resp = jsonify(message="an error occured")
            return (resp, 404)

    else:
        resp = jsonify(message="todo not found")
        return (resp, 404)

    resp = jsonify(deleted=id)
    return (resp)

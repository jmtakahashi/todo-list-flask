import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, flash, jsonify, session, g
from sqlalchemy.exc import IntegrityError

from flask_debugtoolbar import DebugToolbarExtension
from flask_cors import CORS

from forms import TodoAddForm, LoginForm, UserAddForm, UserEditForm, UserDeleteForm
from models import db, connect_db, Todo, User


app = Flask(__name__)
cors = CORS(app)


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

# toolbar = DebugToolbarExtension(app)


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

    if CURR_USER_KEY in session:
        return redirect("/todos")

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
            flash("Account exists please login.", 'error')
            return redirect('/')

        do_login(u)

        return redirect('/todos')

    return render_template('signup.html', form=form)


@app.route('/logout', methods=["POST"])
def logout():
    """Logout from app."""

    if CURR_USER_KEY not in session:
        return redirect("/")

    do_logout()

    flash("Log out successful.", 'success')
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
        flash("Login successful.", "success")
        return redirect("/todos")

    return render_template('index.html', form=form)


###############################################################################
# todos - show todos + add todo - requires auth

@app.route('/todos', methods=['GET', 'POST'])
def show_todos():
    """Show all todos, with the add todo form."""

    if CURR_USER_KEY not in session:
        flash("Please login.", "danger")
        return redirect("/")

    form = TodoAddForm()

    if form.validate_on_submit():
        new_todo = Todo(user_id=g.user.id, todo=form.todo.data)

        try:
            db.session.add(new_todo)
            db.session.commit()

        except IntegrityError as exc:
            flash("Please try adding the todo again.", "error")

        flash("Todo added.", "success")
        return redirect("/todos")

    # todos = Todo.query.filter_by(user_id=g.user.id).order_by("id").all()
    todos = g.user.todos

    # format datetime obj to human readable
    if len(todos) > 0:
        for todo in todos:
            formattedDate = todo.date_added.strftime("%m.%d.%y")
            todo.date_added = formattedDate

    return render_template('todos.html', form=form, todos=todos)


###############################################################################
# user profile - edit profile requires auth

@app.route("/profile", methods=["GET", "POST"])
def edit_profile():
    """Show/handle the user profile editing page.  Require auth!"""

    if CURR_USER_KEY not in session:
        flash("Please login.", "danger")
        return redirect("/")

    editForm = UserEditForm(obj=g.user)
    deleteForm = UserDeleteForm()

    if editForm.validate_on_submit():

        u = User.authenticate(g.user.email, editForm.password.data)

        if u:
            # update the user with the new data
            u.username = editForm.username.data
            u.email = editForm.email.data

            # if user is changing passwords, hash the new pw before commiting
            if editForm.new_password.data:
                password_valid = (len(editForm.new_password.data) > 5)
                if password_valid:
                    new_pw = User.hash_password(editForm.new_password.data)
                    u.password = new_pw
                else:
                    # editForm.new_password.errors = [
                    #     "Field must be at least 6 characters long."]
                    flash(
                        "Password not updated. New password must be at least 6 characters long.", "error")
                    return redirect("/profile")

            try:
                db.session.commit()

            except IntegrityError as exc:
                flash("Email already exists.", "danger")
                return redirect("/profile")

            flash("Your profile has been updated.", "success")
            return redirect("/profile")

        flash("Current password incorrect.", "danger")
        return redirect("/profile")

    return render_template("profile.html", editForm=editForm, deleteForm=deleteForm, user=g.user)


###############################################################################
# user profile - delete profile requires auth

@app.route("/profile/delete", methods=["POST"])
def delete_profile():
    """Delete the user profile.  Require auth!"""

    if CURR_USER_KEY not in session:
        flash("Please login.", "danger")
        return redirect("/")

    deleteForm = UserDeleteForm()

    if deleteForm.validate_on_submit():
        u = User.authenticate(g.user.email, deleteForm.password.data)

        if u:
            try:
                db.session.delete(u)
                db.session.commit()

            except:
                flash("There was an error, please refresh and try again.", "danger")
                return redirect("/profile")

            do_logout()

            flash("Your profile has been deleted.", "danger")
            return redirect("/")

        flash("Incorrect password. Your profile has not been deleted.", "danger")
        return redirect("/profile")


###############################################################################
# api routes - todos

# get todos
@app.route("/api/todos", methods=["GET"])
def get_todos():
    """Get all todos."""

    if CURR_USER_KEY not in session:

        resp = jsonify(message="auth required")
        return (resp, 401)

    user_id = session[CURR_USER_KEY]

    todos = Todo.query.filter_by(user_id=user_id).order_by("id").all()

    # if no todos found, respond with message
    if len(todos) == 0:
        resp = jsonify(message="no todos found")
        return (resp)

    data = [todo.serialize() for todo in todos]
    resp = jsonify(todos=data)
    return (resp)


# add a todo
@app.route("/api/todos", methods=["POST"])
def add_todo():
    """Add a todo. Returns the newly added todo."""

    if CURR_USER_KEY not in session:

        resp = jsonify(message="auth required")
        return (resp, 401)

    user_id = session[CURR_USER_KEY]

    # attempt to get our data from the post request
    data = request.json.get("todo")

    # if the data we need is not in the request, throw an error
    if not data:
        resp = jsonify(message="missing required data")
        return (resp, 400)

    # if data is there, try to add to the db
    new_todo = Todo(user_id=user_id, todo=data)

    try:
        db.session.add(new_todo)
        db.session.commit()

    except:
        resp = jsonify(message="todo not created")
        return (resp, 500)

    # serialize the todo (which now contains "id" and "complete" status),
    # create our resp and return
    data = new_todo.serialize()
    resp = jsonify(todo=data)
    return (resp, 201)


# get a single todo
@app.route("/api/todos/<int:id>", methods=["GET"])
def get_todo(id):
    """Get a single todo by id."""

    if CURR_USER_KEY not in session:

        resp = jsonify(message="auth required")
        return (resp, 401)

    user_id = session[CURR_USER_KEY]

    # get our todo.  if not found, the except block will run
    todo = Todo.query.get(id)

    if todo.user_id == user_id:
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

    if CURR_USER_KEY not in session:

        resp = jsonify(message="auth required")
        return (resp, 401)

    user_id = session[CURR_USER_KEY]

    # get our todo.  if not found, the except block will run
    todo = Todo.query.get(id)

    if todo.user_id == user_id:
        # update our todo with new data, giving default options if the data
        # doesn't exist in the json of the request
        todo.todo = request.json.get("todo", todo.todo)
        todo.complete = request.json.get("complete", todo.complete)

        try:
            db.session.commit()

        except:
            resp = jsonify(message="an error occured")
            return (resp, 500)

    else:
        resp = jsonify(message="not authorized")
        return (resp, 401)

    # serialize the todo, create our resp and return
    data = todo.serialize()
    resp = jsonify(todo=data)
    return (resp)


# delete a todo route
@app.route("/api/todos/<id>", methods=["DELETE"])
def delete_todo(id):
    """Delete a single todo by id."""

    if CURR_USER_KEY not in session:

        resp = jsonify(message="auth required")
        return (resp, 401)

    user_id = session[CURR_USER_KEY]

    todo = Todo.query.get(id)

    if todo:
        if todo.user_id == user_id:
            try:
                db.session.delete(todo)
                db.session.commit()

            except:
                resp = jsonify(message="an error occured")
                return (resp, 500)

        else:
            resp = jsonify(message="not authorized")
            return (resp, 401)

    else:
        resp = jsonify(message="not found")
        return (resp, 404)

    resp = jsonify(deleted=id)
    return (resp)

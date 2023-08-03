import os

from termcolor import colored

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
app.app_context().push()

###############################################################################
# config

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
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

	session[CURR_USER_KEY] = user.username


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
		# if form is valid and submitted try to add our user
		try:
			# send our user info to be registered
			u = User.signup(
				username=form.username.data,
				password=form.password.data,

			)

			# if there's an error in the above method, the except will be thrown

			# the .signup() method in the model will add our user to the session

			# commit our added user
			db.session.commit()

			# after db.session.commit() the user will contain the id from our db
			# do_login() just adds the user to the current session
			do_login(u)

		except IntegrityError as exc:
			flash("Username already exists!", 'danger')
			return render_template('/signup.html', form=form)

		# after we do_login() we redirect to index again, but add_user_to_g() will
		# run and we will have g.user when we redirect to the index page.
		return redirect('/')

	# if form not validated just display the template
	return render_template('signup.html', form=form)

@app.route('/logout', methods=["GET"])
def logout():
	"""Logout from app."""

	do_logout()

	return redirect("/")


###############################################################################
# index route - login, todos/addTodo

@app.route("/", methods=["GET", "POST"])
def home_page():
	"""The home page.  If user is not logged in, show login form, else show todos."""

	login_form = LoginForm()
	todo_form = TodoAddForm()

	if login_form.validate_on_submit():
		try:
			# attempt authentication. we will get back our user or False
			u = User.authenticate(login_form.username.data,
								  login_form.password.data)

			# is u comes back with data, login our user.
			# if u comes back with False, set a flash message
			if u:
				do_login(u)

			else:
				flash("Try again...", 'danger')

		except IntegrityError as exc:
			# if an error occurs, set a flash message
			flash("Try again...", 'danger')
		
		# either way, we need to redirect the user to "/"
		return redirect("/")

	if todo_form.validate_on_submit():
		try:
			# we could utilize the add_todo class method to refactor,
			# but for now we leave everything here to match our api routes.

			# create our new todo instance
			new_todo = Todo(todo=todo_form.todo.data)

			# add our new todo to the session
			db.session.add(new_todo)

			# commit the new todo
			db.session.commit()

		except IntegrityError as exc:
			flash("Please try adding the todo again.", "danger")
			
		# either way, we need to reload the page, but we'll have flash messages
		return redirect("/")

	# initialize a var so we can pass it to the template (python scope issue)
	todos = {}

	# this is additional security to ensure no todos are passed w/o logging in.
	# if we don't check that user is logged in first and simply got all todos,
	# we wouldn't see them on the front-end because we also check using jinja
	# but the todos arg would still be passed to the index.html view.
	# this stops Flask from sending any todos if no user is logged in.
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

		# serialize the todo (which now contains "id" and "done" status), 
		# create our resp and return
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
		# get our todo.  if not found, the except block will run
		todo = Todo.query.get_or_404(id)

		# serialize the todo, create our resp and return
		data = todo.serialize()
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
		# get our todo.  if not found, the except block will run
		todo = Todo.query.get_or_404(id)

		# update our todo with new data, giving default options if the data
		# doesn't exist in the json of the request
		todo.todo = request.json.get("todo", todo.todo)
		todo.done = request.json.get("done", todo.done)

		db.session.commit()

		# serialize the todo, create our resp and return
		data = todo.serialize()
		resp = jsonify(todo=data)
		return (resp)

	except:
		resp = jsonify(message="an error occured")
		return (resp, 404)


# delete a todo route #
@ app.route("/api/todos/<id>", methods=["DELETE"])
def delete_todo(id):
	"""Delete a single todo by id."""

	try:
		# get our todo.  if not found, the except block will run
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

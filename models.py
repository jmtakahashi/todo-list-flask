from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


def connect_db(app):
    db.app = app
    db.init_app(app)


###############################################################################
# Todo class

class Todo(db.Model):
    """Todo model"""

    __tablename__ = "todos"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    todo = db.Column(db.Text, nullable=False)
    done = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Todo {self.id} todo={self.todo} done={self.done}>"

    @classmethod
    def add_todo(cls, todo):
        """Create a new todo."""

        todo = Todo(todo=todo, done=False)

        # add our todo to the session
        db.session.add(todo)

        # db.commit() is done in app.py

        return todo

    def serialize(self):
        """Serialze a todo SQLAlchemy obj to dict."""

        return {
            "id": self.id,
            "todo": self.todo,
            "done": self.done
        }


###############################################################################
# User class

class User(db.Model):
    """User model"""

    __tablename__ = "users"
    username = db.Column(db.Text, primary_key=True)
    password = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

    @classmethod
    def signup(cls, username, password):
        """Create a new user exists and password is correct."""

        # hash our users password with bcrypt
        hashed = bcrypt.generate_password_hash(password)
        hashed_password = hashed.decode("utf8")

        # create our user
        user = User(username=username, password=hashed_password)

        # add our user to the session
        db.session.add(user)

        # db.commit() is done in app.py

        return user

    @classmethod
    def authenticate(cls, username, password):
        """Validate that user exists and password is correct."""

        # return the user if valid, else return false
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            return user
        else:
            return False

    def hash_password(password):
        # hash our users password with bcrypt
        hashed = bcrypt.generate_password_hash(password)
        hashed_pwd = hashed.decode("utf8")
        return hashed_pwd

"""Models for Todo List"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()


def connect_db(app):
    """Connect to the database."""
    db.app = app
    db.init_app(app)


###############################################################################
# User class

class User(db.Model):
    """User model"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)

    todos = db.relationship(
        "Todo", backref="user", order_by='Todo.id.asc()', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} username={self.username} email={self.email}>"

    @classmethod
    def signup(cls, username, email, password):
        """Create a new user exists and password is correct."""

        # hash our users password with bcrypt
        hashed = bcrypt.generate_password_hash(password)
        hashed_password = hashed.decode("utf8")

        user = User(username=username, email=email, password=hashed_password)

        return user

    @classmethod
    def authenticate(cls, email, password):
        """Validate that user exists and password is correct."""

        user = User.query.filter_by(email=email).first()

        # if a user is returned and they password provided matches, return the user
        if user and bcrypt.check_password_hash(user.password, password):
            return user
        else:
            return False

    def hash_password(password):
        # hash our users password with bcrypt
        hashed = bcrypt.generate_password_hash(password)
        hashed_pwd = hashed.decode("utf8")
        return hashed_pwd


###############################################################################
# Todo class

class Todo(db.Model):
    """Todo model"""

    __tablename__ = "todos"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    todo = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.Text, nullable=False, default=datetime.now())
    complete = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Todo id={self.id} owner={self.user_id} todo={self.todo} date_added={self.date_added} complete={self.complete}>"

    def serialize(self):
        """Serialze a todo SQLAlchemy obj to dict."""

        return {
            "id": self.id,
            "user_id": self.user_id,
            "todo": self.todo,
            "date_added": self.date_added,
            "complete": self.complete
        }

"""User model tests."""

# run these tests like:
#    python -m unittest test_user_model.py

from app import app
from unittest import TestCase

from models import db, User, Todo


################################################################################
# testing config

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///todo_list_test"
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
app.config['SQLALCHEMY_ECHO'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


################################################################################
# tests

class UserModelTestCase(TestCase):
    """Test User model."""

    ########################################################################
    # this will run once before all tests run

    # @classmethod
    # def setUpClass(cls) -> None:
    #     return super().setUpClass()

    ########################################################################
    # this will run once after all tests complete

    @classmethod
    def tearDownClass(cls):
        Todo.query.delete()
        User.query.delete()
        db.session.commit()

    ########################################################################
    # this will run before every individual test

    def setUp(self):
        """Create test client, add sample data."""

        # start fresh with no db entries
        Todo.query.delete()
        User.query.delete()

        # add a user to our db to test against
        # use User.signup so password is hashed correctly
        u = User.signup(
            username="TestUser",
            email="test@test.com",
            password="HASHED_PASSWORD",
        )

        db.session.add(u)
        db.session.commit()

        self.user_id = u.id

    ########################################################################
    # this will run after every individual test

    def tearDown(self):
        """Rollback on exit"""

        db.session.rollback()

    ########################################################################
    # testing

    def test_user_model(self):
        """Does the basic user model work?"""

        # add a user, we already have 1 user in the db
        u = User(
            username="TestUser2",
            email="test2@test.com",
            password="HASHED_PASSWORD",
        )

        db.session.add(u)
        db.session.commit()

        # fresh user should have no todos
        self.assertEqual(len(u.todos), 0)

        # User __repr__ should return "<User #{self.user_id}: {self.username}, {self.email}>
        self.assertEqual(
            str(u), f"<User id={u.id} username={u.username} email={u.email}>")

    def test_user_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""

        u = User.signup(
            username="TestUser2",
            email="test2@test.com",
            password="HASHED_PASSWORD",
        )

        db.session.add(u)
        db.session.commit()

        user = User.query.get(u.id)

        self.assertEqual(u, user)

    def test_user_signup_fail_username_missing(self):
        """Does User.signup fail to create a new user if username is null?"""

        # we already have "TestUser" in our db
        u = User(
            email="test@test.com",
            password="HASHED_PASSWORD"
        )

        # this should fail because u1.email is the same as u.email
        db.session.add(u)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_user_signup_fail_email_missing(self):
        """Does User.signup fail to create a new user if email is null?"""

        # we already have "TestUser" in our db
        u = User(
            username="TestUser",
            email="test@test.com",
            password="HASHED_PASSWORD"
        )

        # this should fail because u1.email is the same as u.email
        db.session.add(u)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_user_signup_fail_email_duplicate(self):
        """Does User.signup fail to create a new user if email already exists?"""

        # we already have "TestUser" in our db
        u = User(
            username="TestUser",
            email="test@test.com",
            password="HASHED_PASSWORD"
        )

        # this should fail because u1.email is the same as u.email
        db.session.add(u)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_user_signup_fail_password_missing(self):
        """Does User.signup fail to create a new user if password is missing?"""

        # we already have "TestUser" in our db
        u = User(
            username="TestUser",
            email="test@test.com",
        )

        # this should fail because u1.email is the same as u.email
        db.session.add(u)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_user_authenticate(self):
        """Does User.authenticate() successfully return a user when given a valid email and password?"""

        # get the user that we created on setup so we can test against
        u = User.query.get(self.user_id)

        # check User.authenticate() with the credentials from the original user
        self.assertEqual(User.authenticate(
            email="test@test.com", password="HASHED_PASSWORD"), u)

    def test_user_authenticate_fail_email(self):
        """Does User.authenticate() fail to return a user when the email is invalid?"""

        # we already have "TestUser" in our db, so we test with a diff. email
        self.assertEqual(User.authenticate(
            email="test2@test.com", password="HASHED_PASSWORD"), False)

    def test_user_authenticate_fail_password(self):
        """Does User.authenticate() fail to return a user when the password is invalid?"""

        # we already have "TestUser" in our db, so we test with a diff. pwd
        self.assertEqual(User.authenticate(
            email="test@test.com", password="HSHD_PWD"), False)

    def test_relationship_on_user_model(self):
        """Does the relationship set up on the user model work?
        Can we access a user's todos throught the user model?
        """

        # add a todo with the id of our already added user
        t = Todo(
            user_id=self.user_id,
            todo="test todo list"
        )

        db.session.add(t)
        db.session.commit()

        # get our already created user
        u = User.query.get(self.user_id)

        # we should be able to get the todo through user relationship
        self.assertEqual(u.todos, [t])

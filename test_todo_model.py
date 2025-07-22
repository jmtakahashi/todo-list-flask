"""Todo model tests."""

# run these tests like:
#    python -m unittest test_todo_model.py

from app import app
from unittest import TestCase

from models import db, Todo, User


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

class TodoModelTestCase(TestCase):
    """Test Todo model."""

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

        # start fresh with no db
        Todo.query.delete()
        User.query.delete()

        # create  2 users in our Users model.
        u1 = User(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD",
        )

        u2 = User(
            username="testuser2",
            email="test2@test.com",
            password="HASHED_PASSWORD",
        )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        self.client = app.test_client()

    ########################################################################
    # this will run after every individual test

    def tearDown(self):
        """Rollback on exit"""

        db.session.rollback()

    ########################################################################
    # tests

    def test_todo_model(self):
        """Does basic todo work?"""

        # get our testuser
        u = User.query.filter_by(username="testuser").first()

        # create a todo for our user
        t1 = Todo(
            user_id=u.id,
            todo="Test todo 1",
        )

        db.session.add(t1)
        db.session.commit()

        # User should have 1 todo
        self.assertEqual(len(u.todos), 1)

        # create another todo from the recently created user
        t2 = Todo(
            user_id=u.id,
            todo="Test todo 2",
        )

        db.session.add(t2)
        db.session.commit()

        # User should have 2 todos
        self.assertEqual(len(u.todos), 2)

        # Todos should contain a timestamp in the date_added field
        # self.assertIsInstance(t1.date_added, datetime)
        # self.assertIsInstance(t2.date_added, datetime)

        # Todos should contain false in the completed field
        self.assertEqual(t1.complete, False)
        self.assertEqual(t2.complete, False)

    def test_duplicate_todo_different_user(self):
        """Can duplicate todos be added with different user id's?"""

        # get our users
        u1 = User.query.filter_by(email="test@test.com").first()
        u2 = User.query.filter_by(email="test2@test.com").first()

        # create a movie for user1
        t1 = Todo(
            user_id=u1.id,
            todo="Test todo 2",
        )

        # create the same movie for user2
        t2 = Todo(
            user_id=u2.id,
            todo="Test todo 2",
        )

        db.session.add(t1)
        db.session.add(t2)
        db.session.commit()

        # todo db table should have 2 rows
        self.assertEqual(len(Todo.query.all()), 2)

    def test_fail_on_nonexistent_user_id(self):
        """Does adding a todo fail if a user_id doesn't exist in the user's table?"""

        # get the 2nd  user.  the id should be the highest id in our db.
        u2 = User.query.filter_by(username="testuser2").first()

        # create a movie from the recently created user with a user ID that doesn't exist
        t = Todo(
            user_id=u2.id+1,
            todo="Test todo 2",
        )

        db.session.add(t)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_fail_on_missing_user_id(self):
        """Does adding a todo fail if a user_id field is missing?"""

        # create a todo with a missing user ID in the data
        t = Todo(
            todo="Test todo 2",
        )

        db.session.add(t)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_fail_on_missing_todo(self):
        """Does adding a todo fail if the todo field is missing?"""

        # get the 1st  user.
        u = User.query.filter_by(email="test@test.com").first()

        # create a todo from the recently created user with a missing todo field
        t = Todo(
            user_id=u.id,
        )

        db.session.add(t)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)

    def test_todo_cascade_delete(self):
        """Does the deleting a user also delete the associated todos?"""

        # get our user
        u = User.query.filter_by(email="test@test.com").first()

        # create a todo associated to our user
        t = Todo(
            user_id=u.id,
            todo="Test todo 1",
        )

        db.session.add(t)
        db.session.commit()

        # delete our test user
        db.session.delete(u)
        db.session.commit()

        num_todos = Todo.query.filter_by(user_id=u.id).count()

        # there should be no movies with our user_id in our db
        self.assertEqual(num_todos, 0)

    def test_todo_serialize(self):
        """Does serialize return the correct data?"""

        # get our user
        u = User.query.filter_by(email="test@test.com").first()

        # create a todo associated to our user
        t = Todo(
            user_id=u.id,
            todo="Test todo 1",
        )

        db.session.add(t)
        db.session.commit()

        self.assertEqual(t.serialize(), {
            "id": t.id,
            "user_id": u.id,
            "todo": t.todo,
            "date_added": t.date_added,
            "complete": t.complete
        })

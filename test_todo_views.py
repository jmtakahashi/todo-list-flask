"""Todo View tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_todo_views.py

from app import app, CURR_USER_KEY
from unittest import TestCase

from models import db, User, Todo


################################################################################
# testing config

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///todo_list_test"
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
app.config['SQLALCHEMY_ECHO'] = False

# Don't have WTForms use CSRF at all, since it's a pain to test
app.config['WTF_CSRF_ENABLED'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


################################################################################
# tests

class TodoViewTestCase(TestCase):
    """Test views for movies."""

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

        Todo.query.delete()
        User.query.delete()

        # create an initial user
        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    )

        db.session.add(self.testuser)
        db.session.commit()

        # create an initial todo
        self.testtodo = Todo(
            user_id=self.testuser.id,
            todo="Test todo",
        )

        db.session.add(self.testtodo)
        db.session.commit()

        self.client = app.test_client()

    ########################################################################
    # this will run before every individual test

    def tearDown(self):
        """Rollback on exit"""

        db.session.rollback()

    ########################################################################
    # tests

    def test_todos_get_route_no_auth(self):
        """Test /todos route GET method without being logged in.  
        Are we redirected back to / if not logged in?"""

        with self.client as c:
            resp = c.get("/todos")

            # check that we are redirected if we are not logged in
            self.assertEqual(resp.status_code, 302)

            resp = c.get("/todos", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="login-form" class="loginForm" method="POST">', html)

    def test_todos_get_route_with_auth(self):
        """Test /todos route GET method when logged in. 
        Can we retrieve list of todos?"""

        with self.client as c:
            # Since we need to change the session to mimic logging in,
            # we need to use the changing-session trick:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/todos")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            # check that our todo form is showing up
            self.assertIn(
                '<form id="todo-form" class="todoForm" method="POST">', html)
            # check that our todo is showing up
            self.assertIn("Test todo", html)

    def test_todos_post_route_not_logged_in(self):
        """Test /todos route POST method when not logged in. 
        Are we redirected back to /?"""

        with self.client as c:

            resp = c.post("/todos")

            self.assertEqual(resp.status_code, 302)

            resp = c.post("/todos", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            # check that our logged in username is showing up
            self.assertIn(
                '<form id="login-form" class="loginForm" method="POST">', html)

    def test_todos_post_route_logged_in_no_data(self):
        """Test /todos route POST method when logged in without data sent. 
        Do we show the /todos route correctly?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            data = {}

            resp = c.post("/todos", data=data)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            # check that our logged in username is showing up
            self.assertIn(
                '<form id="todo-form" class="todoForm" method="POST">', html)

    def test_todos_post_route_logged_in_correct_data(self):
        """Test /todos route POST method when logged in with data sent. 
        Is the page correctly refreshed with new todo in the db and on the page?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            data = {"todo": "test todo 2"}

            # this call will create another todo
            resp = c.post("/todos", data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Todo added.', html)
            self.assertIn('test todo 2', html)

            num_todos = Todo.query.filter_by(user_id=self.testuser.id).count()
            self.assertEqual(num_todos, 2)

    def test_delete_todo_ajax_no_auth(self):
        """Test /api/todos/<id> route DELETE method when NOT logged in.
        Do we get the proper response from the api?"""

        with self.client as c:

            resp = c.delete(f"/api/todos/{self.testtodo.id}")

            self.assertEqual(resp.status_code, 401)

    def test_delete_todo_ajax_with_auth(self):
        """Test /api/todos/<id> route DELETE method when logged in.
        Can user delete a todo from the trash can icon?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            t = Todo(
                user_id=self.testuser.id,
                todo="test todo 3"
            )

            db.session.add(t)
            db.session.commit()

            resp = c.delete(f"/api/todos/{t.id}")

            self.assertEqual(resp.status_code, 200)
            # the json we get back will have the id as a string so we need to convert
            self.assertEqual(resp.json, {"deleted": str(t.id)})

            # should have been removed from the db
            self.assertEqual(Todo.query.get(t.id), None)

            resp = c.get("/todos")
            html = resp.get_data(as_text=True)

            # element should have been removed from the page
            self.assertNotIn('test todo 3', html)

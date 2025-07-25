"""User view tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_message_views.py

from flask import session

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

class UserViewTestCase(TestCase):
    """Test views for users."""

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

        self.client = app.test_client()

        # create an initial user
        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="password",
                                    )

        db.session.add(self.testuser)
        db.session.commit()

        # create a todo
        self.testtodo = Todo(
            user_id=self.testuser.id,
            todo="Test todo",
        )

        db.session.add(self.testtodo)
        db.session.commit()

    ########################################################################
    # this will run before every individual test

    def tearDown(self):
        """Rollback on exit"""

        db.session.rollback()

    ########################################################################
    # tests

    def test_homepage_get(self):
        """Test the homepage view GET route when a user is not logged in."""

        with self.client as c:
            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="login-form" class="loginForm" method="POST">', html)

    def test_homepage_get_logged_in(self):
        """Test the homepage view GET route when a user is logged in.  
        Should redirect to /todos"""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/')

            self.assertEqual(resp.status_code, 302)

            resp = c.get('/', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertIn(
                '<form id="todo-form" class="todoForm" method="POST">', html)

    def test_homepage_post_not_logged_in(self):
        """Test the homepage view POST route. This is our login route.  
        Homepage should return the login form."""

        with self.client as c:

            resp = c.post('/', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="login-form" class="loginForm" method="POST">', html)

    def test_homepage_post_logged_in(self):
        """Test the homepage view post route. This is our login route.  
        Does the homepage redirect properly to the todo page, if user is logged in? """

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            data = {
                'email': 'test@test.com',
                'password': 'password'
            }

            # following the redirect to the "/todos" route
            resp = c.post('/', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="todo-form" class="todoForm" method="POST">', html)

    def test_homepage_post_incorrect_login(self):
        """Test the homepage view post route when incorrect credentials are sent.  
        Does the homepage refresh with a correct note?"""

        with self.client as c:
            data = {
                'email': 'test@test.com',
                'password': 'asdfasdfaasdf'
            }

            resp = c.post('/', data=data)

            self.assertEqual(resp.status_code, 302)

            # following the redirect to the "/todos" route
            resp = c.post('/', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertNotIn(CURR_USER_KEY, session)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="login-form" class="loginForm" method="POST">', html)

    def test_homepage_post_correct_login(self):
        """Test the homepage view POST route with correct login credentials sent.  
        Does the homepage redirect user to /todos with user in the session?"""

        with self.client as c:
            data = {
                'email': 'test@test.com',
                'password': 'password'
            }

            resp = c.post('/', data=data)

            self.assertEqual(session[CURR_USER_KEY], self.testuser.id)
            self.assertEqual(resp.status_code, 302)

            # following the redirect to the "/todos" route
            resp = c.post('/', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(session[CURR_USER_KEY], self.testuser.id)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="todo-form" class="todoForm" method="POST">', html)

    def test_signup_get_not_logged_in(self):
        """Test the signup view GET route when not logged in."""

        with self.client as c:
            resp = c.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="todo-list-signup-form" method="POST">', html)

    def test_signup_get_logged_in(self):
        """Test the signup view GET route when a user is already logged in.
        Does the user get redirected to /todos?"""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/signup')

            self.assertEqual(resp.status_code, 302)

            resp = c.get('/signup', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertIn(
                '<form id="todo-form" class="todoForm" method="POST">', html)

    def test_signup_post_not_logged_in(self):
        """Test the signup view POST route if a user is not logged in.
        Should simply display signup form."""

        with self.client as c:
            resp = c.post('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="todo-list-signup-form" method="POST">', html)

    def test_signup_post_logged_in(self):
        """ Test the signup view POST route if user is already logged in. 
        Should redirect to /todos."""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post('/signup')

            # check that our response code is the redirect coming from the view
            self.assertEqual(resp.status_code, 302)

            resp = c.post('/signup', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertIn(
                '<form id="todo-form" class="todoForm" method="POST">', html)

    def test_signup_post_with_correct_data(self):
        """ Test the signup view POST route with required data provided.  
        Should sign the user up, log them in and redirect to /todos."""

        with self.client as c:
            # we already have a user with username "testuser"
            data = {
                'username': 'testuser2',
                'email': 'test2@test.com',
                'password': 'asdfasdfasdfasd',
            }

            resp = c.post('/signup', data=data)

            self.assertIn(CURR_USER_KEY, session)
            self.assertEqual(resp.status_code, 302)

            resp = c.post('/signup', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertIn(CURR_USER_KEY, session)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="todo-form" class="todoForm" method="POST">', html)

            num_users = User.query.all()
            self.assertEqual(len(num_users), 2)

    def test_signup_post_with_missing_data(self):
        """ Test the signup view POST route with missing user provided data. 
        Should show the /signup route as form is not validated."""

        with self.client as c:
            # we already have a user with username "testuser"
            data = {
                'email': 'test2@test.com',
                'password': 'asdfasdfasdfasd',
            }

            resp = c.post('/signup', data=data)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="todo-list-signup-form" method="POST">', html)

    def test_logout_get(self):
        """ Test the logout view GET route. 
        Should return a 405 (Method Not Allowed) response."""

        with self.client as c:
            resp = c.get('/logout')
            self.assertEqual(resp.status_code, 405)

    def test_logout_redirect(self):
        """ Test the logout view POST route if a user is NOT logged in.  
        Should redirect to /."""

        with self.client as c:
            # following the redirect to the "/" route
            resp = c.post('/logout')

            self.assertEqual(resp.status_code, 302)

            resp = c.post('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="login-form" class="loginForm" method="POST">', html)

    def test_logout(self):
        """ Test the logout view POST route while logged in.
        Should log user out and redirect to /."""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post('/logout')
            self.assertEqual(resp.status_code, 302)

            # following the redirect to the "/" route
            resp = c.post('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the home page
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Log out successful", html)

            # check that session has been cleared after running do_logout()
            self.assertNotIn(CURR_USER_KEY, session)

    def test_user_profile_get_no_auth(self):
        """Test /profile GET route while not logged in.
        Should redirect to /."""
        with self.client as c:
            resp = c.get('/profile')

            self.assertEqual(resp.status_code, 302)

            resp = c.get('/profile', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertIn(
                '<form id="login-form" class="loginForm" method="POST">', html)

    def test_user_profile_get_logged_in(self):
        """ Test /profile GET route while logged in.
        Should show the edit profile and delete profile forms."""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # check that the profile page is displayed
            resp = c.get('/profile')
            html = resp.get_data(as_text=True)

            # check our status code
            self.assertEqual(resp.status_code, 200)
            # check that our username is in the html
            self.assertIn(
                ' <form id="profile-edit-form" action="/profile" method="POST">', html)
            self.assertIn(
                ' <form id="profile-delete-form" action="/profile/delete" method="POST">', html)

    def test_user_profile_post_correct_pw(self):
        """ Test our edit profile POST route with correct password.
        This should refresh our /profile page and show the users new info."""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # changing our profile details (except for pw)
            data = {
                'username': 'testuser2',
                'password': 'password',
                'email': 'test2@test.com',
            }

            resp = c.post('/profile', data=data)
            self.assertEqual(resp.status_code, 302)

            resp = c.post('/profile', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the profile page with our new username
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Your profile has been updated.", html)
            self.assertIn("testuser2", html)

    def test_user_profile_post_incorrect_pw(self):
        """ Test our edit profile POST route with incorrect password.
        Should redirect/refresh the page with errors shown."""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # changing our profile details (except for pw)
            data = {
                'username': 'testuser2',
                'email': 'test2@test.com',
                'password': 'incorrectpassword',
            }

            resp = c.post('/profile', data=data)
            self.assertEqual(resp.status_code, 302)

            resp = c.post('/profile', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the profile page with our new username
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Current password incorrect.", html)

    def test_user_profile_post_correct_pw_duplicate_email(self):
        """ Test our edit profile POST route with correct password but email already used.
        Should redirect/refresh the page with errors shown."""
        with self.client as c:
            # create an initial user
            u = User.signup(username="testuser2",
                            email="test2@test.com",
                            password="password",
                            )

            db.session.add(u)
            db.session.commit()

            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = u.id

            # changing our profile details (except for pw), and changing to an email already being used.
            data = {
                'username': 'testuser2',
                'email': 'test@test.com',
                'password': 'password',
            }

            resp = c.post('/profile', data=data)
            self.assertEqual(resp.status_code, 302)

            resp = c.post('/profile', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the profile page with our new username
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Email already exists.", html)

            # check to see that our newly created user's email has not changed
            check = User.query.filter_by(id=u.id).first()
            self.assertEqual(check.email, u.email)

    def test_delete_profile_get_not_logged_in(self):
        """Test the delete profile view GET route while not logged in.
        Should return a 405."""

        with self.client as c:
            resp = c.get('/profile/delete')
            self.assertEqual(resp.status_code, 405)

    def test_delete_profile_get_logged_in(self):
        """Test the delete profile view GET route while logged in.
        Should return a 405."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/profile/delete')
            self.assertEqual(resp.status_code, 405)

    def test_delete_profile_post_not_logged_in(self):
        """Test the delete profile view POST route when user is not logged in.  
        Should redirect to /."""

        with self.client as c:
            resp = c.post('/profile/delete')

            self.assertEqual(resp.status_code, 302)

            resp = c.post('/profile/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="login-form" class="loginForm" method="POST">', html)

    def test_delete_user_correct_pw(self):
        """ Test profile delete POST route with the correct pw.
        Should delete user from db, logout user, and redirect to /."""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            data = {"password": "password"}

            resp = c.post('/profile/delete', data=data)

            self.assertNotIn(CURR_USER_KEY, session)
            self.assertEqual(resp.status_code, 302)

            resp = c.post(
                '/profile/delete', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the home page with our flash message
            self.assertNotIn(CURR_USER_KEY, session)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<form id="login-form" class="loginForm" method="POST">', html)

            # check that our user has been deleted
            num_users = User.query.filter_by(id=self.testuser.id).count()
            self.assertEqual(num_users, 0)

    def test_delete_user_incorrect_pw(self):
        """ Test profile delete POST route with an incorrect pw.
        Should not logout user, and refresh the /profile page with a note."""

        with self.client as c:
            # we should be logged in for this route, so we add our test user_id to the session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # incorrect password
            data = {"password": "drowssap"}

            resp = c.post('/profile/delete', data=data)

            self.assertEqual(session[CURR_USER_KEY], self.testuser.id)
            # check that we are redirected to the edit profile page
            self.assertEqual(resp.status_code, 302)

            resp = c.post('/profile/delete', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(session[CURR_USER_KEY], self.testuser.id)
            # check that we are redirected back to the profile page
            self.assertIn(
                '<form id="profile-edit-form" action="/profile" method="POST">', html)
            self.assertIn(
                'Incorrect password. Your profile has not been deleted', html)

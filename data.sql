-- in terminal: 
--   psql < data.sql
--   psql [database_name]

DROP DATABASE IF EXISTS todo_list;
CREATE DATABASE todo_list;

DROP DATABASE IF EXISTS todo_list_test;
CREATE DATABASE todo_list_test;

-- uncomment below for production environment
-- \c todo_list
-- uncomment below for development environment
-- \c todo_list_test

DROP TABLE users;
DROP TABLE todos;

CREATE TABLE users
(
  id SERIAL PRIMARY KEY, 
  username TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL, 
  password TEXT NOT NULL
);

CREATE TABLE todos
(
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  todo TEXT NOT NULL, 
  date_added TIMESTAMP NOT NULL, 
  complete BOOLEAN NOT NULL DEFAULT false
);
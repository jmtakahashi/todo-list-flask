-- in terminal: 
--   psql < data.sql
--   psql [database_name]

DROP DATABASE IF EXISTS todo_list;
CREATE DATABASE todo_list;

-- for supabse
-- \c postgres

-- for local or other
\c todo_list

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
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  todo TEXT NOT NULL, 
  date_added TIMESTAMP NOT NULL, 
  complete BOOLEAN NOT NULL DEFAULT false
);

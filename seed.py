# run using 
#   $ python seed.py

from models import db, Todo, User
from app import app

db.drop_all()
db.create_all()
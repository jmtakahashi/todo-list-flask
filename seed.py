"""SEED file to make sample data for the database """

# run using:
#   $ python seed.py

from models import db
from app import app

db.drop_all()
db.create_all()

"""Utility file to seed database with """

from sqlalchemy import func
from model import User
from model import Rating
from model import Movie

from model import connect_to_db, db
from server import app
from datetime import datetime


def load_users():
    """Load base categories from seed-user.txt into database."""

    print("Users")

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    User.query.delete()

    # Read seed category file and insert data
    for row in open("seed-user.txt"):
        row = row.rstrip()
        email, password = row.split("|")

        user = User(email=email,
                    password=password)

        # We need to add to the session or it won't ever be stored
        db.session.add(base_category)

    # Once we're done, we should commit our work
    db.session.commit()


def load_categories():
    """Load base categories from seed-category.txt into database."""

    print("Base Categories")

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    BaseCategory.query.delete()

    # Read seed category file and insert data
    for row in open("seed-category.txt"):
        row = row.rstrip()
        base_category_id, name, description = row.split("|")

        base_category = BaseCategory(base_category_id=base_category_id,
                    name=name,
                    description=description)

        # We need to add to the session or it won't ever be stored
        db.session.add(base_category)

    # Once we're done, we should commit our work
    db.session.commit()

if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import data
    load_categories
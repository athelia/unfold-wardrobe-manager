"""Utility file to seed database"""

from sqlalchemy import func

# Import helper function, SQLAlchemy database, and model definitions
from model import (connect_to_db, db, User, BaseCategory, Category, Article,
    Outfit, Tag, ArticleOutfit, TagArticle, TagOutfit)

from server import app
from datetime import datetime


def load_users():
    """Load base categories from seed-user.txt into database."""

    print("Users")

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    User.query.delete()

    # Read seed category file and insert data
    for row in open("seed/seed-user.txt"):
        row = row.rstrip()
        user_id, email, password = row.split("|")

        user = User(user_id=user_id,
                    email=email.lower(), # Cast to lowercase
                    password=password)

        # We need to add to the session or it won't ever be stored
        db.session.add(user)

    # Once we're done, we should commit our work
    db.session.commit()


def load_base_categories():
    """Load base categories from seed-category.txt into database."""

    print("Base Categories")

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    BaseCategory.query.delete()

    # Read seed category file and insert data
    for row in open("seed/seed-category.txt"):
        row = row.rstrip()
        base_category_id, name, description = row.split("|")

        base_category = BaseCategory(base_category_id=base_category_id,
                                     name=name,
                                     description=description)
        db.session.add(base_category)
    db.session.commit()


def load_user_categories():
    """Load user categories from seed-user-category.txt into database."""

    print("User Categories")

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    Category.query.delete()

    # Read seed category file and insert data
    for row in open("seed/seed-user-category-2.txt"):
        row = row.rstrip()
        # Works for original seed data
        # user_id, base_category_id, name, description = row.split("|")

        # These are metadata lines in the file
        if not row.startswith('--'):
            category_id, name, description, user_id, base_category_id = row.split("|")

            category = Category(category_id=int(category_id),
                                name=name,
                                description=description,
                                user_id=int(user_id),
                                base_category_id=base_category_id)
            db.session.add(category)
    db.session.commit()


def load_articles():
    """Load articles from seed-article.txt into database."""

    print("Articles")

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    Article.query.delete()

    # Read seed category file and insert data
    for row in open("seed/seed-article-2.txt"):
        row = row.rstrip()
        # Works for original seed data 
        # user_id, category_id, description = row.split("|")

        # These are metadata lines in the file
        if not row.startswith('--'):
            article_id, description, image, purchase_price, times_worn, sell_price, user_id, category_id = row.split("|")
            
            # Prevent passing an empty string into field expecting float
            if not purchase_price:
                purchase_price = None
            
            article = Article(article_id=int(article_id),
                              description=description,
                              image=image,
                              purchase_price=purchase_price,
                              times_worn=times_worn,
                              user_id=int(user_id),
                              category_id=int(category_id),
                              )
            db.session.add(article)
    db.session.commit()


def load_tags():
    """Load tags from seed-tag.txt into database."""

    print("Tags")

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    Tag.query.delete()

    # Read seed category file and insert data
    for row in open("seed/seed-tag.txt"):
        row = row.rstrip()
        user_id, name = row.split("|")

        tag = Tag(user_id=int(user_id),
                  name=name)

        # We need to add to the session or it won't ever be stored
        db.session.add(tag)

    # Once we're done, we should commit our work
    db.session.commit()


def set_val_user_id():
    """Set value for the next user_id after seeding database"""

    # Get the Max user_id in the database
    result = db.session.query(func.max(User.user_id)).one()
    max_id = int(result[0])

    # Set the value for the next user_id to be max_id + 1
    query = "SELECT setval('users_user_id_seq', :new_id)"
    db.session.execute(query, {'new_id': max_id + 1})
    db.session.commit()


def set_val_category_id():
    """Set value for the next category_id after seeding database"""

    # Get the Max category_id in the database
    result = db.session.query(func.max(Category.category_id)).one()
    max_id = int(result[0])

    # Set the value for the next category_id to be max_id + 1
    query = "SELECT setval('categories_category_id_seq', :new_id)"
    db.session.execute(query, {'new_id': max_id + 1})
    db.session.commit()


if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import data
    load_users()
    load_base_categories()
    load_user_categories()
    load_articles()
    load_tags()

    # Update IDs to reflect imported data
    set_val_user_id()
    set_val_category_id()
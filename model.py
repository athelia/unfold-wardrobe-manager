"""Models & db functions for wardrobe manager project."""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, update

db = SQLAlchemy()

class User(db.Model):
    """User of wardrobe manager website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return f"<User ID={self.user_id} Email={self.email}>"


class Category(db.Model):
    """Standard category of clothing articles."""

    __tablename__ = "categories"

    category_id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        return f"<Category ID={self.category_id} Name={self.name}>"


class UserCategory(db.Model):
    """User defined categories of clothing articles, inheriting from standard categories."""

    __tablename__ = "users_categories"

    user_category_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    category_id = db.Column(db.String(10), db.ForeignKey('categories.category_id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=True)

    # Define relationship to Category
    category = db.relationship("Category", backref=db.backref("users_categories"))

    def __repr__(self):
        return f"<UserCategory ID={self.user_category_id} Name={self.name}>"


class Article(db.Model):
    """Article of clothing."""

    __tablename__ = "articles"

    article_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    user_category_id = db.Column(db.Integer, db.ForeignKey('users_categories.user_category_id'), nullable=False)
    description = db.Column(db.String(256), nullable=True)
    image = db.Column(db.String(), nullable=True)
    purchase_price = db.Column(db.Float, nullable=True)
    times_worn = db.Column(db.Integer, default=int(0), nullable=False)
    sell_price = db.Column(db.Float, nullable=True)

    # Define relationship to UserCategory
    user_category = db.relationship("UserCategory", backref=db.backref("articles"))

    # Define relationship to Outfit


    # Define relationship to TagArticle


    def __repr__(self):
        return f"<Article ID={self.article_id} Category={self.user_category.name} Description={self.description:.15}>"


class Outfit(db.Model):
    """Outfit composed of articles."""
    
    __tablename__ = "outfits"

    outfit_id = db.Column(db.Integer, autoincrement=True, primary_key=True)


    #Define relationship to TagOutfit

    
    def __repr__(self):
        pass


class Tag(db.Model):
    """Tag for articles and outfits."""
    
    __tablename__ = "tags"

    tag_id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    def __repr__(self):
        pass


class TagArticle(db.Model):
    """Association table for tags and articles."""
    
    __tablename__ = "tags_articles"

    tag_article_id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    def __repr__(self):
        pass


class TagOutfit(db.Model):
    """Association table for tags and outfits."""
    
    __tablename__ = "tags_outfits"

    tag_outfit_id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    def __repr__(self):
        pass
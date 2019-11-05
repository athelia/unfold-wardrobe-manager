"""Models & db functions for wardrobe manager project."""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, update

db = SQLAlchemy()

##############################################################################
# Model definitions

class User(db.Model):
    """User of wardrobe manager website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return f"<User ID={self.user_id} Email={self.email}>"


class BaseCategory(db.Model):
    """Standard categories of clothing articles."""

    __tablename__ = "base_categories"

    base_category_id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        return f"<Category ID={self.category_id} Name={self.name}>"


class UserCategory(db.Model):
    """User defined categories of clothing articles, inheriting from standard categories."""

    __tablename__ = "users_categories"

    user_category_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    base_category_id = db.Column(db.String(10), db.ForeignKey('base_categories.base_category_id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=True)

    # Define relationship to Category
    base_category = db.relationship('BaseCategory', backref=db.backref('users_categories'))

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
    times_worn = db.Column(db.Integer, default=0, nullable=False)
    sell_price = db.Column(db.Float, nullable=True)

    # Define relationship to UserCategory
    user_category = db.relationship('UserCategory', backref=db.backref('articles'))


    # Define relationship to TagArticle
    tag_article = db.relationship('TagArticle', backref=db.backref('articles'))

    def __repr__(self):
        return f"<Article ID={self.article_id} Category={self.user_category.name} Description={self.description:.15}>"


class Outfit(db.Model):
    """Outfit composed of articles."""
    
    __tablename__ = "outfits"

    outfit_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    description = db.Column(db.String(256), nullable=True)
    times_worn = db.Column(db.Integer, default='0', nullable=False)

    def __repr__(self):
        return f"<Outfit ID={self.outfit_id} Name={self.name} Description={self.description:.15}>"


class ArticleOutfit(db.Model):
    """Association table for articles and outfits."""

    __tablename__ = "articles_outfits"

    article_outfit_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.article_id'), nullable=False)
    outfit_id = db.Column(db.Integer, db.ForeignKey('outfits.outfit_id'), nullable=False)

    # Define relationship to Article
    article = db.relationship('Article', backref=db.backref('articles_outfits'))

    # Define relationship to Outfit
    outfit = db.relationship('Outfit', backref=db.backref('articles_outfits'))

    def __repr__(self):
        return f"<ArticleOutfit ID={self.article_outfit_id} Article ID={self.article_id} Outfit ID={self.outfit_id}>"


class Tag(db.Model):
    """Tag for articles and outfits."""
    
    __tablename__ = "tags"

    tag_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name = db.Column(db.String(32), nullable=False)

    def __repr__(self):
        return f"<Tag ID={self.tag_id} Name={self.name}>"


class TagArticle(db.Model):
    """Association table for tags and articles."""
    
    __tablename__ = "tags_articles"

    tag_article_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.article_id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.tag_id'), nullable=False)

    # Define relationship to Tag
    tag = db.relationship('Tag', backref=db.backref('tags_articles'))

    # Define relationship to Article
    article = db.relationship('Article', backref=db.backref('tags_articles'))

    def __repr__(self):
        return f"<TagArticle ID={self.tag_article_id} Tag ID={self.tag_id} Article ID={self.article_id}>"


class TagOutfit(db.Model):
    """Association table for tags and outfits."""
    
    __tablename__ = "tags_outfits"

    tag_outfit_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    outfit_id = db.Column(db.Integer, db.ForeignKey('outfits.outfit_id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.tag_id'), nullable=False)

    # Define relationship to Tag
    tag = db.relationship('Tag', backref=db.backref('tags_outfits'))

    # Define relationship to Outfit
    outfit = db.relationship('Outfit', backref=db.backref('tags_outfits'))

    def __repr__(self):
        return f"<TagOutfit ID={self.tag_outfit_id} Tag ID={self.tag_id} Outfit ID={self.outfit_id}>"


##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///clothes'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app 
    connect_to_db(app)
    print("Connected to DB.")

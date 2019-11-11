"""Models & db functions for wardrobe manager project."""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, update

db = SQLAlchemy()

##############################################################################
# Model definitions

class User(db.Model):
    """User of wardrobe manager website."""

    __tablename__ = 'users'

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)

    # Define relationships to Article and Outfit
    articles = db.relationship('Article', backref='user')
    outfits = db.relationship('Outfit', backref='user')

    def update(self, attribute_name, new_attribute):
        """Update the category's information."""

        if attribute_name == 'email':
          self.email = new_attribute
        elif attribute_name == 'password':
          self.password = new_attribute
        db.session.commit()

    # ~CODE REVIEW~
    def delete(self):
        """Remove the user."""

        # First remove all foreign key dependencies
        for outfit in self.outfits:
            for article in outfit.articles:
                outfit.remove(article)
            del(outfit)

        for article in self.articles:
            del(article)

        for category in self.categories:
            del(category)

        del(self)
        db.session.commit()

    def __repr__(self):
        return f'<user_id={self.user_id} email={self.email}>'


class Category(db.Model):
    """User defined categories of clothing articles, inheriting from standard categories."""

    __tablename__ = 'categories'

    category_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=True)

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.user_id'),
                        nullable=False)
    base_category_id = db.Column(db.String(10), 
                                 db.ForeignKey('base_categories.base_category_id'), 
                                 nullable=False)

    # Define relationship to BaseCategory and Article
    base_category = db.relationship('BaseCategory', backref='categories')
    articles = db.relationship('Article', backref='category')

    def update(self, attribute_name, new_attribute):
        """Update the category's information."""

        if attribute_name == 'name':
          self.name = new_attribute
        elif attribute_name == 'description':
          self.description = new_attribute
        db.session.commit()

    # ~CODE REVIEW~
    def delete(self):
        """Remove the category."""

        # First remove all foreign key dependencies
        for article in self.articles:
            article.remove(self)

        del(self)
        db.session.commit()

    def __repr__(self):
        return f'<category_id={self.category_id} name={self.name}>'


class Article(db.Model):
    """Article of clothing."""

    __tablename__ = 'articles'

    article_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    description = db.Column(db.String(256), nullable=True)
    image = db.Column(db.String(), nullable=True)
    purchase_price = db.Column(db.Float, nullable=True)
    times_worn = db.Column(db.Integer, default=0, nullable=False)
    sell_price = db.Column(db.Float, nullable=True)

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.user_id'),
                        nullable=False)
    category_id = db.Column(db.Integer,
                            db.ForeignKey('categories.category_id'),
                            nullable=False)

    # Define relationship to Tag
    tags = db.relationship('Tag',
                           backref='articles',
                           secondary='tags_articles')

    #############################
    # ~CODE REVIEW~ 
    # 
    # def update(self, category=self.category, description=self.description,
    #            purchase_price=self.purchase_price):
    #     """Update the article's information."""

    #     self.category_id = category.category_id
    #     self.description = description
    #     self.purchase_price = purchase_price
    #     db.session.commit()

    def update(self, attribute_name, new_attribute):
        """Update the article's information."""

        # self.f'{attribute_name}' = new_attribute
        # self.attribute_name = new_attribute
        # f'{self}.{attribute_name}' = new_attribute
        if attribute_name == 'category_id':
          self.category_id = new_attribute
        elif attribute_name == 'description':
          self.description = new_attribute
        elif attribute_name == 'purchase_price':
          self.purchase_price = new_attribute
        db.session.commit()

    # ~CODE REVIEW~
    def delete(self):
        """Remove the article."""

        # First remove all foreign key dependencies
        for outfit in self.outfits:
            outfit.remove(self)

        del(self)
        db.session.commit()

    def __repr__(self):
        return f'<article_id={self.article_id} \
                  category.name={self.category.name} \
                  description={self.description:.15}>'


class Outfit(db.Model):
    """Outfit composed of articles."""
    
    __tablename__ = 'outfits'

    outfit_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(64), nullable=True)
    description = db.Column(db.String(256), nullable=True)
    times_worn = db.Column(db.Integer, default='0', nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    # Define relationship to Article and Tag
    articles = db.relationship('Article', 
                               backref='outfits', 
                               secondary='articles_outfits')
    tags = db.relationship('Tag',
                           backref='outfits',
                           secondary='tags_outfits')

    # Outfit update methods: update, add_article, remove_article
    def update(self, attribute_name, new_attribute):
        """Update the category's information."""

        if attribute_name == 'name':
            self.name = new_attribute
        elif attribute_name == 'description':
            self.description = new_attribute
        elif attribute_name == 'times_worn':
            self.times_worn = new_attribute
        db.session.commit()

    def add_article(self, article):
        """Add the article to the outfit."""

        # TODO: check if an article of a cateogry doesn't alrady exist
        self.articles.append(article)
        db.session.commit()

    def remove_article(self, article):
        """Remove the article from the outfit."""

        self.articles.remove(article)
        db.session.commit()

    # ~CODE REVIEW~
    # Outfit delete method
    def delete(self):
        """Remove the outfit."""

        # First remove all foreign key dependencies
        for article in self.articles:
            article.remove(self)

        del(self)
        db.session.commit()

    # Assorted outfit methods
    def calculate_value(self):
        """Sum value of all articles in the outfit."""
        
        sum = 0
        for article in self.articles:
            sum += article.purchase_price
        return sum

    def is_category_in_outfit(self, category):
        for article in self.articles:
            if article.category_id == category.category_id:
                return True
        return False

    def __repr__(self):
        return f'<outfit_id={self.outfit_id} \
                  name={self.name} \
                  description={self.description:.15}>'


class Tag(db.Model):
    """Tag for articles and outfits."""
    
    __tablename__ = 'tags'

    tag_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(32), nullable=False)

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.user_id'),
                        nullable=False)

    def __repr__(self):
        return f'<Tag ID={self.tag_id} Name={self.name}>'


class BaseCategory(db.Model):
    """Standard categories of clothing articles."""

    __tablename__ = 'base_categories'

    base_category_id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        return f'<base_category_id={self.base_category_id} name={self.name}>'


class ArticleOutfit(db.Model):
    """Association table for articles and outfits."""

    __tablename__ = 'articles_outfits'

    article_outfit_id = db.Column(db.Integer,
                                  autoincrement=True,
                                  primary_key=True)
    article_id = db.Column(db.Integer,
                           db.ForeignKey('articles.article_id'),
                           nullable=False)
    outfit_id = db.Column(db.Integer,
                          db.ForeignKey('outfits.outfit_id'),
                          nullable=False)

    def __repr__(self):
        return f'<article_outfit_id={self.article_outfit_id} \
                  article_id={self.article_id} \
                  outfit_id={self.outfit_id}>'


class TagArticle(db.Model):
    """Association table for tags and articles."""
    
    __tablename__ = 'tags_articles'

    tag_article_id = db.Column(db.Integer,
                               autoincrement=True,
                               primary_key=True)
    article_id = db.Column(db.Integer,
                           db.ForeignKey('articles.article_id'),
                           nullable=False)
    tag_id = db.Column(db.Integer,
                       db.ForeignKey('tags.tag_id'),
                       nullable=False)

    def __repr__(self):
        return f'<tag_article_id={self.tag_article_id} \
                  tag_id={self.tag_id} \
                  article_id={self.article_id}>'


class TagOutfit(db.Model):
    """Association table for tags and outfits."""
    
    __tablename__ = 'tags_outfits'

    tag_outfit_id = db.Column(db.Integer,
                              autoincrement=True,
                              primary_key=True)
    outfit_id = db.Column(db.Integer,
                          db.ForeignKey('outfits.outfit_id'),
                          nullable=False)
    tag_id = db.Column(db.Integer,
                       db.ForeignKey('tags.tag_id'),
                       nullable=False)

    def __repr__(self):
        return f'<tag_outfit_id={self.tag_outfit_id} \
                  tag_id={self.tag_id} \
                  outfit_id={self.outfit_id}>'


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


if __name__ == '__main__':
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app 
    connect_to_db(app)
    print('Connected to DB.')

"""Models & db functions for wardrobe manager project."""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, update
from datetime import datetime as dt
import os
from darksky import forecast

db = SQLAlchemy()

dark_sky = ({
    'secret':os.environ.get('DARK_SKY_API_SECRET'),
    })

##############################################################################
# Model definitions

class User(db.Model):
    """User of wardrobe manager website.
    
    >>> dr_horrible = User(user_id = 0, email = 'blog@phd-in-horribleness.com', \
        password = 'talktoPennyTODAY')
    >>> dr_horrible
    <user_id=0 email=blog@phd-in-horribleness.com>
    """

    __tablename__ = 'users'

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)

    # Define relationships to Article, Outfit, and Category
    articles = db.relationship('Article', backref='user',
                               cascade='all, delete, delete-orphan')
    outfits = db.relationship('Outfit', backref='user',
                              cascade='all, delete, delete-orphan')
    categories = db.relationship('Category', backref='user',
                                 cascade='all, delete, delete-orphan')
    wear_events = db.relationship('WearEvent', backref='user',
                                  cascade='all, delete, delete-orphan')

    def update(self, options):
        """Update the user's information."""

        self.email = options.get('email', self.email)
        self.password = options.get('password', self.password)
        db.session.commit()

    # TODO: learn about cascade delete as in relationships above, then remove
    # the remove-all-user-data functionality in delete().
    def delete(self):
        """Remove the user."""

        # First remove all of a user's data
        # ? self.outfits.delete()
        # ? Outfit.query.filter_by(user_id=self.user_id).delete()

        # ?
        outfits.delete().where(outfits.user_id == self.user_id)
        articles.delete().where(articles.user_id == self.user_id)
        categories.delete().where(categories.user_id == self.user_id)

        # Not good:
        # for outfit in self.outfits:
        #     db.session.delete(outfit)
        # for article in self.articles:
        #     db.session.delete(article)
        # for category in self.categories:
        #     db.session.delete(category)

        # Then remove the account
        db.session.delete(self)
        db.session.commit()

    def calculate_value(self):
        """Sum value of all articles a user owns."""
        
        sum = 0
        for article in self.articles:
            sum += article.purchase_price
        return sum

    def get_counts_of_users_items(self):
        """Count all of a user's outfits, articles, categories, and tags."""

        # TODO: set up instance attribute stats somewhere else besides here :(
        self.stats = {}
        self.stats['counts'] = {
                                    'outfits': 0,
                                    'articles': 0,
                                    'categories': 0,
                                    'tags': 0,
                                    }

        # if not self.stats.get('counts'):
        #     self.stats['counts'] = {
        #                             'outfits': 0,
        #                             'articles': 0,
        #                             'categories': 0,
        #                             'tags': 0,
        #                             }

        # TODO: refactor using something related to COUNT from SQLAlchemy
        qty_outfits = len(self.get_outfits_query().all())
        qty_articles = len(self.get_articles_query().all())
        qty_categories = len(self.get_categories_query().all())
        qty_tags = len(self.get_tags_query().all())

        self.stats['counts']['outfits'] = qty_outfits
        self.stats['counts']['articles'] = qty_articles
        self.stats['counts']['categories'] = qty_categories
        self.stats['counts']['tags'] = qty_tags

        return self.stats

    def get_categories_query(self):
      """Start a query for all of a user's categories."""
      
      categories_query = Category.query.filter_by(user_id = self.user_id)
      return categories_query

    def get_articles_query(self):
      """Start a query for all of a user's articles."""
      
      articles_query = Article.query.filter_by(user_id = self.user_id)
      return articles_query

    def get_outfits_query(self):
      """Query for all of a user's outfits."""
      
      outfits_query = Outfit.query.filter_by(user_id = self.user_id)
      return outfits_query

    def get_tags_query(self):
      """Query for all of a user's tags."""
      
      tags_query = Tag.query.filter_by(user_id = self.user_id)
      return tags_query

    def __repr__(self):
        return f'<user_id={self.user_id} email={self.email}>'


class Category(db.Model):
    """User defined categories of clothing articles, inheriting from standard categories.
    
    >>> lab_coats = Category(category_id = 0, name = 'Lab Coats', description = \
        'Classic length lab coats', user_id = 0, base_category_id = 'fulls')
    >>> lab_coats
    <category_id=0 name=Lab Coats>
    >>> gloves = Category(category_id = 1, name = 'Gloves', description = \
        'Chemical resistant 18" gloves', user_id = 0, base_category_id = 'others')
    >>> gloves
    <category_id=1 name=Gloves>
    """

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

    def update(self, options):
        """Update the category's information."""

        self.name = options.get('name', self.name)
        self.description = options.get('description', self.description)
        db.session.commit()

    # TODO: Warn if articles become orphaned as a result.
    # Best refactoring would be allowing a user to select some/all via filters
    # and reassign to a new category.
    def delete(self):
        """Remove the category."""

        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<category_id={self.category_id} name={self.name}>'


class Article(db.Model):
    """Article of clothing.
    
    NOTE - The repr will throw an AttributeError if created in Repl because the 
    relationship between article and category does not exist.

    >>> std_lab_coat = Article(article_id = 0, image = 'white_coat.png', \
        description = '41" white lab coat with 3 button closure', \
        purchase_price = 48.99, times_worn = 3, user_id = 0, category_id = 0)
    >>> std_lab_coat
    <article_id=0 category_name=Lab Coats description=41" white lab c>
    >>> std_lab_coat.description
    '41" white lab coat with 3 button closure'

    >>> white_gloves = Article(article_id = 1, image = 'white_gloves.png', \
        description = '18" white work gloves', purchase_price = 8.99, \
        times_worn = 3, user_id = 0, category_id = 1)
    >>> white_gloves
    <article_id=1 category_name=Gloves description=18" white work >
    >>> white_gloves.times_worn
    3
    """

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

    def update(self, options):
        """Update the article's information.

        >>> white_gloves.update({'purchase_price': 7.99})
        >>> white_gloves.purchase_price
        7.99
        """

        self.category_id = options.get('category_id', self.category_id)
        self.description = options.get('description', self.description)
        self.purchase_price = options.get('purchase_price', self.purchase_price)
        self.sell_price = options.get('sell_price', self.sell_price)

        db.session.commit()

    def add_tag(self, tag):
        """Add the tag to the article."""

        self.tags.append(tag)
        db.session.commit()

    def remove_tag(self, tag):
        """Remove the tag from the article."""

        self.tags.remove(tag)
        db.session.commit()

    def delete(self):
        """Remove the article."""

        db.session.delete(self)
        db.session.commit()

    def incr_times_worn(self):
        """Increase times_worn attribute.
        
        >>> white_gloves.times_worn
        3
        >>> white_gloves.incr_times_worn()
        >>> white_gloves.times_worn
        4
        """

        self.times_worn += 1
        db.session.commit()

    def __repr__(self):
        return f'<article_id={self.article_id} \
                  category.name={self.category.name} \
                  description={self.description:.15}>'


class Outfit(db.Model):
    """Outfit composed of articles.
    
    >>> work_outfit = Outfit(outfit_id = 0, name = 'Work Outfit 1', \
        description = 'White coat, white gloves, goggles, and work boots', \
        times_worn = 3, user_id = 0)
    >>> work_outfit
    <outfit_id=0 name=Work Outfit 1 description=White coat, whi>

    """
    
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
    wear_events = db.relationship('WearEvent',
                                  backref='outfits')

    # Outfit update methods: update, add_article, remove_article
    def update(self, options):
        """Update the outfit's information."""

        self.name = options.get('name', self.name)
        self.description = options.get('description', self.description)
        self.times_worn = options.get('times_worn', self.times_worn)
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

    def add_tag(self, tag):
        """Add the tag to the outfit."""

        self.tags.append(tag)
        db.session.commit()

    def remove_tag(self, tag):
        """Remove the tag from the outfit."""

        self.tags.remove(tag)
        db.session.commit()

    # Outfit delete method
    def delete(self):
        """Remove the outfit."""

        db.session.delete(self)
        db.session.commit()

    # Assorted outfit methods
    def calculate_value(self):
        """Sum value of all articles in the outfit."""
        
        sum = 0
        for article in self.articles:
            sum += article.purchase_price
        return sum

    def incr_times_worn(self):
        """Increase times_worn attribute."""

        self.times_worn += 1
        for article in self.articles:
            article.incr_times_worn()

        db.session.commit()

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

    def parse_str_to_tag(tag_string, user_id):
        """Convert comma-sep string to Tag objects."""

        new_tags = []

        if tag_string:
            tags = tag_string.split(',')
            for idx, tag_name in enumerate(tags):
                tag_name.lstrip()
                tag = Tag(user_id=user_id,
                          name=tag_name)
                new_tags.append(tag)
                # db.session.add(tag)

        # db.session.commit()
        # Return new tags so we can create relationships with them
        return new_tags

    def update(self, options):
        """Update the tag's information."""

        self.name = options.get('name', self.name)
        db.session.commit()

    def delete(self):
        """Remove the tag."""

        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<tag_id={self.tag_id} name={self.name}>'


class WearEvent(db.Model):
    """Instances of outfits being worn. Can be past or future; outfits can be added later."""
    
    __tablename__ = 'wear_events'

    wear_event_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(256), nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    temperature = db.Column(db.Float, nullable=True)
    weather_cond = db.Column(db.String(128), nullable=True)

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.user_id'),
                        nullable=False)
    outfit_id = db.Column(db.Integer,
                          db.ForeignKey('outfits.outfit_id'),
                          nullable=True) # Outfit can be added after creation

    # Define relationship to Tag
    tags = db.relationship('Tag',
                           backref='wear_events',
                           secondary='tags_events')

    def update(self, options):
        """Update the event's information."""

        self.name = options.get('name', self.name)
        self.description = options.get('description', self.description)
        self.date = options.get('date', self.date)
        self.outfit_id = options.get('outfit_id', self.outfit_id)
        db.session.commit()

    def set_weather(self, lat=37.774929, lng=-122.419418):
        """Assign temperature and weather conditions for date at latitude & longitude.
            
            >>> new_evt = WearEvent(wear_event_id=0, name='Party', \
            description='Birthday party at Monarch', date=dt(2019, 11, 16, 20, 30), \
            user_id=1)
            >>> new_evt
            <wear_event_id=0 name=Party user_id=1>
            >>> key = ####### 
            >>> dark_sky['secret'] = key
            >>> sflat=37.774929
            >>> sflng=-122.419418
            >>> new_evt.set_weather(sflat, sflng)
            >>> new_evt.temperature
            58.77
            >>> new_evt.weather_cond
            'Clear'
        """

        # Dark Sky requires a date in isoformat
        weather = forecast(dark_sky['secret'], lat, lng, time=self.date.isoformat())
        self.temperature = weather.temperature
        self.weather_cond = weather.summary
        db.session.commit()

    # WIP
    def match_tags(self):
        """Compare event's tags to outfit tags."""

        for tag in self.tags:
            # Are there outfits with the same tag?
            # If so add all to a dictionary with a counter += 1
            # Return dictionary
            pass

    def add_tag(self, tag):
        """Add the tag to the event."""

        self.tags.append(tag)
        db.session.commit()

    def remove_tag(self, tag):
        """Remove the tag from the event."""

        self.tags.remove(tag)
        db.session.commit()

    def delete(self):
        """Remove the event."""

        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<wear_event_id={self.wear_event_id} name={self.name} user_id={self.user_id}>'


class BaseCategory(db.Model):
    """Standard categories of clothing articles."""

    __tablename__ = 'base_categories'

    base_category_id = db.Column(db.Unicode(10), primary_key=True)
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


class TagEvent(db.Model):
    """Association table for tags and events."""
    
    __tablename__ = 'tags_events'

    tag_event_id = db.Column(db.Integer,
                              autoincrement=True,
                              primary_key=True)
    wear_event_id = db.Column(db.Integer,
                          db.ForeignKey('wear_events.wear_event_id'),
                          nullable=False)
    tag_id = db.Column(db.Integer,
                       db.ForeignKey('tags.tag_id'),
                       nullable=False)

    def __repr__(self):
        return f'<tag_outfit_id={self.tag_outfit_id} \
                  tag_id={self.tag_id} \
                  wear_event_id={self.wear_event_id}>'


##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///clothes'
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///testclothes'
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
    # db.create_all()

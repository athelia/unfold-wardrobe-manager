"""Models & db functions for wardrobe manager project."""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, update
from datetime import date, timedelta, datetime as dt
import os
from darksky import forecast
import textwrap

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
    events = db.relationship('WearEvent', backref='user',
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
        # Should be unnecessary with cascade-delete above, 
        # remove once testing complete

        # Less good approach:
        # for outfit in self.outfits:
        #     db.session.delete(outfit)
        # for article in self.articles:
        #     db.session.delete(article)
        # for category in self.categories:
        #     db.session.delete(category)

        # Maybe works?
        # ? self.outfits.delete()
        # ? Outfit.query.filter_by(user_id=self.user_id).delete()

        outfits.delete().where(outfits.user_id == self.user_id)
        articles.delete().where(articles.user_id == self.user_id)
        categories.delete().where(categories.user_id == self.user_id)

        # Then remove the account
        db.session.delete(self)
        db.session.commit()

    def calculate_value(self):
        """Sum value of all articles a user owns."""
        
        sum = 0
        for article in self.articles:
            sum += article.purchase_price
        return sum

    def get_stats(self):
        """Count all of a user's outfits, articles, categories, and tags."""

        # TODO: set up instance attribute stats somewhere else besides here :(
        self.stats = {}
        self.stats['counts'] = {}
        self.stats['most_worn'] = {}
        self.stats['best_value'] = {}
        self.stats['most_used'] = {}

        # TODO: refactor using something related to COUNT from SQLAlchemy
        self.__get_outfit_stats__()
        self.__get_article_stats__()
        self.__get_tag_stats__()
        self.__get_category_stats__()
        self.__get_event_stats__()

        return self.stats

    def __get_outfit_stats__(self):
        """Stats for user's outfits."""

        # TODO: refactor using something related to COUNT from SQLAlchemy
        outfits = self.get_outfits_query().order_by(Outfit.times_worn).all()
        self.stats['counts']['outfits'] = len(outfits)

        if outfits:
            self.stats['most_worn']['outfit'] = outfits[-1]

            best_value = outfits[-1].calculate_value()
            best_nonzero_value = -1

            for outfit in outfits:
                if outfit.times_worn > 0:
                    value = outfit.calculate_value() / outfit.times_worn
                    outfit.value = value
                    if outfit.value < best_value:
                        best_value = outfit.value
                        self.stats['best_value']['outfit'] = outfit

                    # Store the first nonzero outfit value, then store any subsequent 
                    # value better than it
                    if outfit.value > 0 and (best_nonzero_value == -1 or 
                                             outfit.value < best_nonzero_value):
                        best_nonzero_value = outfit.value
                        self.stats['best_value']['nonzero_outfit'] = outfit

    def __get_article_stats__(self):
        """Stats for user's articles."""

        # TODO: refactor using something related to COUNT from SQLAlchemy
        articles = self.get_articles_query().order_by(Article.times_worn).all()
        self.stats['counts']['articles'] = len(articles)

        if articles:
            self.stats['most_worn']['article'] = articles[-1]

            best_value = articles[-1].purchase_price
            best_nonzero_value = -1

            for article in articles:
                if article.times_worn > 0 and type(article.purchase_price) == float:
                    value = article.purchase_price / article.times_worn
                    article.value = value
                    if article.value < best_value:
                        best_value = article.value
                        self.stats['best_value']['article'] = article

                    # Store the first nonzero article value, then store any subsequent 
                    # value better than it
                    if article.value > 0 and (best_nonzero_value == -1 or 
                                             article.value < best_nonzero_value):
                        best_nonzero_value = article.value
                        self.stats['best_value']['nonzero_article'] = article

    def __get_category_stats__(self):
        """Stats for user's categories."""

        categories = self.get_categories_query().all()
        self.stats['counts']['categories'] = len(categories)

        for category in categories:
            # Reset for every loop of categories
            best_value = 0
            best_nonzero_value = -1
            articles = Article.query.filter(Article.category_id == category.category_id).order_by(Article.times_worn).all()
            if articles:
                self.stats['most_worn'][category.name] = articles[-1]
                # Set best_value to a purchase price of an article the list, possibly 0
                best_value = articles[-1].purchase_price
                self.stats['best_value'][category.name] = {'article': None,
                                                           'nonzero_article': None}
                
                for article in articles:
                    if article.times_worn > 0 and type(article.purchase_price) in [float, int]:
                        article.value = article.purchase_price / article.times_worn
                        if article.value < best_value:
                            best_value = article.value
                            self.stats['best_value'][category.name]['article'] = article

                        # Store the first nonzero article value, then store any subsequent 
                        # value better than it
                        if article.value > 0 and (best_nonzero_value == -1 or \
                                                  article.value < best_nonzero_value):
                            best_nonzero_value = article.value
                            self.stats['best_value'][category.name]['nonzero_article'] = article

    def __get_event_stats__(self):
        """Stats for user's events."""

        events = self.get_events_query().all()
        self.stats['counts']['events'] = len(events)

    def __get_tag_stats__(self):
        """Stats for user's tags."""

        tags = self.get_tags_query().all()
        self.stats['counts']['tags'] = len(tags)
        self.stats['most_used']['article'] = {}
        self.stats['most_used']['outfit'] = {}
        self.stats['most_used']['event'] = {}

        tag_article_count = 0
        tag_outfit_count = 0
        tag_event_count = 0

        if tags:
            # TODO: refactor using MAX or a heap data structure
            # Or another table?
            for tag in tags:
                count_ta = TagArticle.query.filter(TagArticle.tag_id == tag.tag_id).count()
                count_to = TagOutfit.query.filter(TagOutfit.tag_id == tag.tag_id).count()
                count_te = TagEvent.query.filter(TagEvent.tag_id == tag.tag_id).count()
                if count_ta > tag_article_count:
                    tag_article_count = count_ta
                    self.stats['most_used']['article']['tag'] = tag
                    self.stats['most_used']['article']['count'] = count_ta
                if count_to > tag_outfit_count:
                    tag_outfit_count = count_to
                    self.stats['most_used']['outfit']['tag'] = tag
                    self.stats['most_used']['outfit']['count'] = count_to
                if count_te > tag_event_count:
                    tag_event_count = count_te
                    self.stats['most_used']['event']['tag'] = tag
                    self.stats['most_used']['event']['count'] = count_te

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

    def get_events_query(self):
        """Query for all of a user's events."""
      
        events_query = WearEvent.query.filter_by(user_id = self.user_id)
        return events_query

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

    # Dedent doesn't work! White space is not eliminated :(
    # def __repr__(self):
    #     return textwrap.dedent(
    #             f'<article_id={self.article_id} \
    #             category.name={self.category.name} \
    #             description={self.description:.20}>'
    #             )
    def __repr__(self):
        return f'<article_id={self.article_id} category.name={self.category.name} description={self.description:.20}>'

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
    events = db.relationship('WearEvent',
                                  backref='outfit')

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
            if article.purchase_price:
                sum += article.purchase_price
        return sum

    def incr_times_worn(self):
        """Increase times_worn attribute."""

        self.times_worn += 1
        for article in self.articles:
            article.incr_times_worn()

        db.session.commit()

    def is_category_in_outfit(self, category):
        """Returns whether an article of the given category exists in the outfit."""
        for article in self.articles:
            if article.category_id == category.category_id:
                return True
        return False

    def count_category_articles(self, category):
        """For the given category, count articles belonging to that category in outfit."""
        count = 0
        for article in self.articles:
            if article.category_id == category.category_id:
                count += 1
        return count

    def last_worn(self):
        """Return last date an outfit was worn."""

        # What was the most recent wear date of top_outfit:
        wear_dates = WearEvent.query.filter_by(outfit_id = self.outfit_id).order_by(WearEvent.date).all()

        if wear_dates:
            return wear_dates[-1]
        else:
            return None

    def __repr__(self):
        return f'<outfit_id={self.outfit_id} name={self.name} description={self.description:.20}>'


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


# TODO: 1) Modify table to increase name column from 32 -> 128 char
# TODO: 2) Replace WearEvent / wear_events -> Event / events
# TODO: 3) Add a precipitation chance column
# TODO: 4) Add icon column (icon most reliable "summary")
class WearEvent(db.Model):
    """Instances of outfits being worn. Can be past or future; outfits can be added later."""
    
    __tablename__ = 'wear_events'

    wear_event_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256), nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    temperature = db.Column(db.Float, nullable=True)
    weather_cond = db.Column(db.String(128), nullable=True)
    # precip_probability = db.Column(db.Float, nullable=True)
    # weather_icon = db.Column(db.String(128), nullable=True)

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.user_id'),
                        nullable=False)
    outfit_id = db.Column(db.Integer,
                          db.ForeignKey('outfits.outfit_id'),
                          nullable=True) # Outfit can be added after creation

    # Define relationship to Tag
    tags = db.relationship('Tag',
                           backref='events',
                           secondary='tags_events')

    def update(self, options):
        """Update the event's information."""

        self.name = options.get('name', self.name)
        self.description = options.get('description', self.description)
        self.date = options.get('date', self.date)
        self.outfit_id = options.get('outfit_id', self.outfit_id)
        db.session.commit()

    # TODO: After #3/4 above, set precip chance and icon instance attributes.
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
        weather = forecast.Forecast(dark_sky['secret'], lat, lng, time=self.date.isoformat())
        self.temperature = weather.temperature
        self.weather_cond = weather.summary
        # self.weather_icon = weather.icon
        # self.precip_probability = weather.precipProbability
        db.session.commit()

    # TODO: If outfit has been worn this week, it has a lower priority.
    # Perhaps the outfit_dict should sort by quanity of tags matched and return 
    # in this order so we can move down the list as options are eliminated.
    def match_tags(self):
        """Compare event's tags to outfit tags. Dictionary returns all matches.

        Matches are stored as 
            outfit: [<tag1>, <tag2>...] 
        and as 
            tag_count (e.g. 3): [<outfit1>, <outfit2>...]
        with one special key 'top_pick'
            'top_pick': <outfit8>
        """

        outfit_dict = {}
        outfit_dict['top_pick'] = ''
        outfit_dict['all_picks'] = []

        if self.tags: 
            most_tags = 0

            for tag in self.tags:
                for outfit in tag.outfits:
                    outfit_dict[outfit] = outfit_dict.get(outfit, [])
                    outfit_dict[outfit].append(tag)
                    outfit_dict[len(outfit_dict[outfit])] = outfit_dict.get(len(outfit_dict[outfit]), [])
                    outfit_dict[len(outfit_dict[outfit])].append(outfit)
                    if len(outfit_dict[outfit]) > 1:
                        outfit_dict[len(outfit_dict[outfit]) - 1].remove(outfit)
                    if len(outfit_dict[outfit]) > most_tags:
                        most_tags = len(outfit_dict[outfit])
                        outfit_dict['top_pick'] = (outfit)

            for i in range(1, most_tags + 1):
                for outfit in outfit_dict[i]:
                    outfit_dict['all_picks'].append(outfit)

        else:
            print('Event has no tags!')
            return None

        return outfit_dict

    # If self.date within 1 week of last worn for outfit_dict's top pick, 
    # look at all other items with same number of tags
    # e.g. outfit_dict[3] = [outfit1, outfit2, outfit3] 
    # eliminate outfit1, worn this week; look at outfit2
    # if not worn this week, replace top_pick.
    # top_pick = outfit_dict['top_pick'] and then get 
    def remove_recent_outfits(self, outfit_dict):
        """Iterate through all_picks removing any outfits worn in last week.

        >>> event = WearEvent.query.get(58)
        >>> od1 = event.match_tags()
        >>> od2 = event.remove_recent_outfits(od1)
        """
        
        delta = timedelta(days=7)
        outfit_dict2 = {}
        outfit_dict2['all_picks'] = list(outfit_dict['all_picks'])
        outfit_dict2['top_pick'] = outfit_dict['top_pick']
        # if outfit_dict['top_pick'].last_worn() <= self.date - delta:

        for outfit in outfit_dict2['all_picks']:
            if outfit.last_worn() != None:
                print(outfit.outfit_id)
                print(outfit.last_worn().date)
                print(self.date - delta)
                if outfit.last_worn().date >= self.date - delta:
                    outfit_dict2['all_picks'].remove(outfit)
                    if outfit == outfit_dict2['top_pick']:
                        outfit_dict2['top_pick'] = None
            else:
                continue

        if outfit_dict2['top_pick']:
            return outfit_dict2
        else:
            outfit_dict2['top_pick'] = outfit_dict2['all_picks'][-1]
            return outfit_dict2
        # if outfit_dict['top_pick'].last_worn() <= self.date - delta:
        #     del outfit_dict['top_pick']
        #     next_pick = outfit_dict[max_tags].get(outfit_dict[max_tags], None)
        #     if next_pick:
        #         outfit_dict['top_pick'] = next_pick
        #     else:
        #         max_tags -= 1
        #         outfit_dict['top_pick'] = outfit_dict[max_tags].get(outfit_dict[max_tags], None)
        #     self.remove_recent_outfits(outfit_dict)

    def recommend_coats(self):
        """Logic for recommending extra layers."""

        coat_count = 0

        precip_set = {
                      "rain",
                      "raining",
                      "drizzle",
                      "snow",
                      "snowing",
                      "sleet",
                      "sleeting",
                      "hail",
                      "hailing",
                      "storm",
                      "storms",
                      "thunderstorm",
                      "thunderstorms",
                      "rainstorm",
                      "rainstorms",
                      "shower",
                      "showers"
                      }
        weather_condition_set = set(self.weather_cond.split())

        if (precip_set & weather_condition_set):
            coat_count = 1

        if self.temperature >= 70:
            pass
        elif self.temperature >= 60:
            coat_count = 1
        elif self.temperature >= 45:
            coat_count += 1
        else:
            coat_count += 2

        return coat_count

    def filter_outfits_by_weather_and_recent(self):
        """Combine match_tags(), remove_recent_outfits(), & recommend_coats() for a final recommendation.

        >>> event = WearEvent.query.get(58)
        >>> result = event.filter_outfits_by_weather_and_recent()
        >>> result
        {'all_picks': [
                       <outfit_id=21 name= description=>,
                       <outfit_id=23 name= description=Green sweater, white>,
                       <outfit_id=25 name= description=Poncho + henley>,
                       <outfit_id=33 name= description=>,
                       <outfit_id=64 name= description=>
                       ], 
        'top_pick': <outfit_id=64 name= description=>
        }
        """

        outfit_dict = self.match_tags()
        if outfit_dict:
            outfit_dict2 = self.remove_recent_outfits(outfit_dict)
            coat_count = self.recommend_coats() if self.weather_cond else 0
            get_outerwear_categories = Category.query.filter(Category.base_category_id == 'outers').all()

            count_of_outerwear = 0
            
            outfit_dict3 = recursive_filter(coat_count, outfit_dict2, get_outerwear_categories)

            if outfit_dict3:
                return outfit_dict3

            else:
                # TODO: recommend a non-weather-appropriate outfit and print text suggesting a jacket
                # Better implementation would suggest a new outfit created from a top_pick 
                # and one or more jackets as appropriate. 
                outfit_dict2['top_pick'] = None
                return outfit_dict2
        else:
            return None

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


def recursive_filter(coat_count, outfit_dict, category_list):
    """Recursively walks through outfit_dict to look for a match with enough coats."""

    count_of_outerwear = 0
    for category in category_list:
        count_of_outerwear += outfit_dict['top_pick'].count_category_articles(category)
        print(f'category={category.name}, count={count_of_outerwear}')

    if count_of_outerwear >= coat_count:
        # First base case is when there are enough coats present
        return outfit_dict
    elif len(outfit_dict['all_picks']) < 1:
        # Second base case is when we run out of outfits
        return None
    else:
        print(f"old top pick={outfit_dict['top_pick']}, new top pick={outfit_dict['all_picks'][-1]}")
        outfit_dict['top_pick'] = outfit_dict['all_picks'][-1]
        outfit_dict['all_picks'].pop()
        recursive_filter(coat_count, outfit_dict, category_list)


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
        return f'<tag_article_id={self.tag_article_id} tag_id={self.tag_id} article_id={self.article_id}>'


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
        return f'<tag_outfit_id={self.tag_outfit_id} tag_id={self.tag_id} outfit_id={self.outfit_id}>'


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
        return f'<tag_outfit_id={self.tag_outfit_id} tag_id={self.tag_id} wear_event_id={self.wear_event_id}>'


##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///clothes'
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///testclothes'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # app.config['SQLALCHEMY_ECHO'] = True
    db.app = app
    db.init_app(app)


if __name__ == '__main__':
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app 
    connect_to_db(app)
    print('Connected to DB.')
    # db.create_all()

"""Web app for wardrobe management"""

from jinja2 import StrictUndefined
from flask import Flask, render_template, redirect, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.utils import secure_filename

import os
import requests
from datetime import datetime, date, timedelta
from sqlalchemy import asc, update, func
import random

import flask_restless
from flask_login import LoginManager

# Import helper function, SQLAlchemy database, and model definitions
from model import (connect_to_db, db, User, BaseCategory, Category, Article,
    Outfit, Tag, WearEvent, ArticleOutfit, TagArticle, TagOutfit, TagEvent)

# Handles image upload and storage
import cloudinary
from cloudinary.uploader import upload

#########################
# REFACTOR ME
# Import functions for image storage and processing
from image_handling import allowed_file, ALLOWED_EXTENSIONS

# CITIES' latitude and longitude
from global_var import CITIES, MONTHS

# Compare clothing prices
from etsy import Etsy

# Get weather from OpenWeatherMap API
import pyowm

# Get weather from DarkSky API
from darksky import forecast

app = Flask(__name__)
app.config.from_pyfile('flaskconfig.cfg')

manager = flask_restless.APIManager(app)

# Set Cloudinary API configuration from environmental variables
cloudinary.config.update = ({
    'cloud_name':os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'api_key': os.environ.get('CLOUDINARY_API_KEY'),
    'api_secret': os.environ.get('CLOUDINARY_API_SECRET')
    })

# Set Etsy API config from environmental variables
etsy_config = ({
    'api_key': os.environ.get('ETSY_API_KEY'),
    'api_secret': os.environ.get('ETSY_API_SECRET')
    })
# Manual assignment of API key
etsy_api = Etsy(etsy_config['api_key'])

# Set OpenWeatherMap API key
owm = pyowm.OWM(os.environ.get('OPEN_WEATHER_API_KEY'))

# Set DarkSky API key
dark_sky = ({
    'secret':os.environ.get('DARK_SKY_API_SECRET'),
    })

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined

# Flask-Login is WIP
# # Flask-Login needs some setup
# login_manager = LoginManager()
# login_manager.init_app(app)


# Flask-Login is WIP
# AttributeError: type object 'User' has no attribute 'get'
# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.filter(User.user_id == user_id).first()


###############################################################################
#                                                                             #
#                                BASIC ROUTES                                 #
#                                                                             #
###############################################################################


# TODO: consistent single quotes in render_template template names
@app.route('/')
def index():
    """If logged in, display homepage to go to outfits, categories, or articles."""
    
    if session.get('user_id', None):
        city = CITIES['SFO']
        # Dark Sky requires a date in isoformat
        weather = forecast(dark_sky['secret'], city['lat'], city['lng'])
        hourly = weather.hourly
        daily = weather.daily

        # Hard-code UTC-8 because haven't implemented proper time zone 
        # localization (yet, anyway)
        # TODO: User can set time zone in profile
        time_offset = - 8 * 60 * 60

        for hour in hourly:
            hour.datestr = datetime.utcfromtimestamp(hour['time'] + time_offset).strftime('%m/%d %H:%M')
        for day in daily:
            day.datestr = datetime.utcfromtimestamp(day['time'] + time_offset).strftime('%m/%d')

        now = datetime.today()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        today_end = datetime(now.year, now.month, now.day, 23, 59, 59)
        events = WearEvent.query.filter(WearEvent.user_id == session['user_id'])
        events_today = events.filter(today_start <= WearEvent.date)
        events_today = events_today.filter(WearEvent.date <= today_end).order_by(WearEvent.date).all()

        outfits = Outfit.query.filter(Outfit.user_id == session['user_id']).all()
        user = User.query.get(session['user_id'])
        categories = Category.query.filter(Category.user_id == session['user_id']).all()
        categories = sort_categories_by_base(categories)
        # TODO: Find a way to save results of this function so the crazy Tag queries
        # don't run every time user goes back to homepage
        # session['user_stats'] = user_stats
        user_stats = user.get_stats()
        random_category = user.categories[random.randint(0,len(user.categories)-1)] \
            if user.categories else None
        random_category2 = user.categories[random.randint(0,len(user.categories)-1)] \
            if user.categories else None
        random_tag = ['article', 'outfit', 'event'][random.randint(0,2)]
        
        # TODO: add the other outfit recs as options at subsequent indices
        # outfit_recs[event] = [top_pick, other option, different option...]
        outfit_recs = {}
        coat_count = None
        for event in events_today:
            filtered = event.filter_outfits_by_weather_and_recent()
            if filtered['top_pick']: 
                outfit_recs[event] = filtered['top_pick']
            else:
                outfit_recs[event] = filtered['all_picks'][-1]
                coat_count = event.recommend_coats()

        return render_template("homepage.html",
                               hourly = hourly,
                               daily = daily,
                               events_today = events_today,
                               outfit_recs = outfit_recs,
                               outfits = outfits,
                               user_stats = user_stats,
                               random_category = random_category,
                               random_category2 = random_category2,
                               random_tag = random_tag,
                               coat_count = coat_count or None
                               )
    else:
        return render_template("login.html")


@app.route('/login')
def login():
    """Check login credentials against database."""

    # Cast to lowercase to match database.
    email = request.args.get('email').lower()
    password = request.args.get('password')

    # Using .first() to return a none-type if not valid
    user = User.query.filter(User.email == email, User.password == password).first()

    if user:
        # Add user's id and email to session
        session['user_id'] = user.user_id
        session['user_email'] = user.email
        # Flask-Login is WIP
        # login_user(user)
        user = User.query.get(session['user_id'])
        flash(f"Welcome back, {session['user_email']}!")
        return redirect('/')
    else:
        flash("Invalid email & password combination. Please try again.")
        return redirect('/')


@app.route('/logout')
def logout():
    """Log user out of session."""

    # Remove user's id and email from session
    del session['user_id']
    del session['user_email']
    # Flask-Login is WIP
    # login_user(user)
    flash(f"Logged out successfully.")
    return redirect('/')


# WIP - This template does not exist!
@app.route('/create-account')
def create_account_page():
    """Display account creation form."""

    return render_template("new-account.html")


# WIP
@app.route('/profile')
def show_profile():
    """Display logged-in user's profile."""

    if session.get('user_id'):
        user = User.query.filter_by(user_id = session['user_id']).one()
    else:
        user = None

    return render_template('profile.html', user = user)


###############################################################################
#                                                                             #
#                           CATEGORIES ROUTES                                 #
#                                                                             #
###############################################################################


@app.route('/categories')
def show_categories():
    """Display all user categories and the option to add a new category."""

    categories = Category.query.filter(Category.user_id == session['user_id']).all()
    base_categories = BaseCategory.query.all()

    return render_template("categories.html", 
                           categories=categories,
                           base_categories=base_categories)


@app.route('/categories/<category_id>')
def show_category_articles(category_id):
    """Display articles of clothing belonging to selected category."""

    # TODO: Possible refactor is to save repetitive queries to a variable &
    # only execute inside the route
    articles = Article.query.filter(Article.category_id == category_id,
                                    Article.user_id == session['user_id']).all()
    category = Category.query.filter(Category.category_id == category_id,
                                     Category.user_id == session['user_id']).one()

    return render_template("single-category.html", 
                           articles=articles,
                           category=category)


@app.route('/add-category')
def show_create_category_form():
    """Display form to create a new user category."""

    base_categories = BaseCategory.query.all()

    return render_template("add-category.html",
                           base_categories=base_categories)


@app.route('/create-category', methods=['POST'])
def add_category():
    """Adds new user-created category and redirects to /categories."""

    name = request.form.get('category-name')
    base_category = request.form.get('base-category')
    description = request.form.get('category-description')

    new_category = Category(user_id =session['user_id'],
                            base_category_id =base_category,
                            name =name,
                            description =description)

    db.session.add(new_category)
    db.session.commit()

    flash(f"Created {new_category.name} successfully")

    return redirect('/categories')


###############################################################################
#                                                                             #
#                             ARTICLES ROUTES                                 #
#                                                                             #
###############################################################################


@app.route('/articles')
def show_articles():
    """Display all articles of clothing and the option to add a new article."""

    categories = Category.query.filter(Category.user_id == session['user_id']).all()
    categories = sort_categories_by_base(categories)
    articles = Article.query.filter(Article.user_id == session['user_id']).all()

    return render_template("articles.html", 
                           articles=articles,
                           categories=categories)


@app.route('/add-article')
def show_create_article_form():
    """Display form to create a new article of clothing."""

    categories = Category.query.filter(Category.user_id == session['user_id']).all()
    tags = Tag.query.filter(Tag.user_id == session['user_id']).all()

    return render_template("add-article.html",
                           categories=categories,
                           tags=tags)


@app.route('/create-article', methods=['POST'])
def add_article():
    """Adds new clothing article and redirects to the previous category page."""

    category_id = request.form.get('category')
    description = request.form.get('article-description')
    file = request.files['article-image-upload']
    tag_ids = request.form.getlist('article-tags')
    new_tag_string = request.form.get('new-tags')
    purchase_price = request.form.get('purchase-price') 

    category = Category.query.get(category_id)

    if not allowed_file(file.filename):
        flash(f'File extension .{file.filename.rsplit(".", 1)[1]} not allowed')
    if file and allowed_file(file.filename):
        
        # Sanitizes user input
        filename = secure_filename(file.filename)

        # Cloudinary upload function: 1) folders by user and category name, 
        # 2) unique filename is true, 
        # 3) use cloudinary's AI to remove background 
        # ^ (commented out b/c paid service)
        upload_file = upload(file,
                             folder = f"user/{session['user_email']}/{category.name}",
                             unique_filename = 1,
                             # background_removal = "cloudinary_ai",
                             )

        # For purchase_price, an empty string not ok, but okay to pass None
        new_article = Article(user_id = session['user_id'],
                              category_id = category_id,
                              image = upload_file['secure_url'],
                              description = description,
                              purchase_price = purchase_price or None)

        all_tags = []
        for tag_id in tag_ids:
            all_tags.append(Tag.query.filter_by(tag_id = tag_id).one())

        # Any newly created tags should be added to this as well
        all_tags += Tag.parse_str_to_tag(new_tag_string, session['user_id'])

        # Then create all the tag relationships
        for tag in all_tags:
            new_article.add_tag(tag)

        db.session.add(new_article)
        db.session.commit()
        flash(f"Created new item in {category.name}")

    return redirect(f'/categories/{category_id}')


@app.route('/delete-article', methods=['POST'])
def delete_article():
    """Deletes an article."""

    article_id = request.form.get('article-to-delete')
    article = Article.query.filter_by(article_id = article_id).one()

    article.delete()

    return redirect('/articles')


@app.route('/articles/<article_id>')
def show_article_detail(article_id):
    """Display specific article details."""

    article = Article.query.filter_by(article_id = article_id).first()
    tags = Tag.query.filter(Tag.user_id == session['user_id']).all()

    return render_template("single-article.html", 
                           article=article,
                           tags=tags)


@app.route('/update-article', methods=['POST'])
def update_article_details():
    """Updates an article's details."""

    new_price = request.form.get('purchase-price')
    article_id = request.form.get('article-to-edit')
    tag_ids = request.form.getlist('article-tags')
    new_tag_string = request.form.get('new-tags')
    article = Article.query.filter_by(article_id = article_id).one()

    if new_price:
        article.update({'purchase_price' : new_price})

    all_tags = []
    for tag_id in tag_ids:
        all_tags.append(Tag.query.filter_by(tag_id = tag_id).one())

    # TODO: Brute force method - remove all tags before appending
    # Better: Check for discrepancies; remove unchecked, then proceed

    # Any newly created tags should be added to this as well
    all_tags += Tag.parse_str_to_tag(new_tag_string, session['user_id'])

    # Then create all the tag relationships
    for tag in all_tags:
        article.add_tag(tag)

    return redirect(f'/articles/{article_id}')


###############################################################################
#                                                                             #
#                              OUTFITS ROUTES                                 #
#                                                                             #
###############################################################################


@app.route('/outfits')
def show_outfits():
    """Display all outfits and the option to add a new outfit."""

    outfits = Outfit.query.filter(Outfit.user_id == session['user_id']).all()

    return render_template('outfits.html', outfits=outfits)


@app.route('/add-outfit')
def show_create_outfit_form():
    """Display form to create a new outfit."""

    categories = Category.query.filter(Category.user_id == session['user_id']).all()
    tags = Tag.query.filter(Tag.user_id == session['user_id']).all()

    return render_template('add-outfit.html', categories=categories, tags=tags)


@app.route('/create-outfit', methods=['POST'])
def add_outfit():
    """Adds new outfit and redirects to the previous outfits page."""

    description = request.form.get('outfit-description')
    name = request.form.get('outfit-name')
    article_ids = request.form.getlist('articles-to-add')
    tag_ids = request.form.getlist('outfit-tags')
    new_tag_string = request.form.get('new-tags')

    # First create a new Outfit in the db
    outfit = Outfit(user_id=session['user_id'],
                    description=description,
                    name=name)
    db.session.add(outfit)

    # Then create all the article relationships
    for article_id in article_ids:
        article = Article.query.filter(Article.article_id == article_id).one()
        outfit.add_article(article)

    all_tags = []
    for tag_id in tag_ids:
        all_tags.append(Tag.query.filter_by(tag_id = tag_id).one())

    # Any newly created tags should be added to this as well
    all_tags += Tag.parse_str_to_tag(new_tag_string, session['user_id'])

    # Then create all the tag relationships
    for tag in all_tags:
        outfit.add_tag(tag)

    db.session.commit()

    text = name if name else description

    flash(f"Created new outfit: {text}")

    return redirect('/outfits')


@app.route('/outfits/<outfit_id>')
def show_outfit_detail(outfit_id):
    """Display specific outfit details."""

    outfit = Outfit.query.filter_by(outfit_id = outfit_id).first()
    categories = Category.query.filter(Category.user_id == session['user_id']).all()
    categories = sort_categories_by_base(categories)
    tags = Tag.query.filter(Tag.user_id == session['user_id']).all()

    return render_template('single-outfit.html',
                           outfit=outfit,
                           categories=categories,
                           tags=tags)


def sort_categories_by_base(categories):
    """Puts user categories in order by base category type."""

    categories_2 = []

    for category in categories:
        if category.base_category_id == 'tops':
            categories_2.append(category)

    for category in categories:
        if category.base_category_id == 'bottoms':
            categories_2.append(category)

    for category in categories:
        if category.base_category_id == 'fulls':
            categories_2.append(category)

    for category in categories:
        if category.base_category_id == 'outers':
            categories_2.append(category)

    for category in categories:
        if category.base_category_id == 'shoes':
            categories_2.append(category)
        elif category.base_category_id == 'hats':
            categories_2.append(category)
        elif category.base_category_id == 'access':
            categories_2.append(category)
        elif category.base_category_id == 'jewels':
            categories_2.append(category)
        elif category.base_category_id == 'others':
            categories_2.append(category)

    return categories_2


@app.route('/update-outfit', methods=['POST'])
def update_outfit_details():
    """Updates an outfit's details."""

    outfit_id = request.form.get('outfit-to-edit')
    new_tag_string = request.form.get('new-tags')
    tag_ids = request.form.getlist('outfit-tags')
    outfit = Outfit.query.filter_by(outfit_id = outfit_id).one()

    all_tags = []
    for tag_id in tag_ids:
        all_tags.append(Tag.query.filter_by(tag_id = tag_id).one())

    # Any newly created tags should be added to this as well
    all_tags += Tag.parse_str_to_tag(new_tag_string, session['user_id'])

    # Then create all the tag relationships
    for tag in all_tags:
        outfit.add_tag(tag)

    return redirect(f'/outfits/{outfit_id}')


@app.route('/delete-outfit', methods=['POST'])
def delete_outfit():
    """Deletes an outfit."""

    outfit_id = request.form.get('outfit-to-delete')
    outfit = Outfit.query.filter_by(outfit_id = outfit_id).one()

    outfit.delete()

    return redirect('/outfits')


@app.route('/add-article/<outfit_id>/<article_id>')
def add_article_to_outfit(outfit_id, article_id):
    """Add article to outfit and update the page."""
    
    outfit = Outfit.query.filter(Outfit.outfit_id == outfit_id).one()
    article = Article.query.filter(Article.article_id == article_id).one()

    outfit.add_article(article)
    categories = Category.query.filter(Category.user_id == session['user_id']).all()

    return redirect(f'/outfits/{outfit_id}')


@app.route('/remove-article/<outfit_id>/<article_id>')
def remove_article_from_outfit(outfit_id, article_id):
    """Remove article from outfit and update the page."""

    outfit = Outfit.query.filter(Outfit.outfit_id == outfit_id).one()
    article = Article.query.filter(Article.article_id == article_id).one()

    outfit.remove_article(article)

    return redirect(f'/outfits/{outfit_id}')


###############################################################################
#                                                                             #
#                               EVENTS ROUTES                                 #
#                                                                             #
###############################################################################


@app.route('/events')
def show_events():
    """Display all events and the option to add a new event."""

    evt_by_month = {}
    # events = WearEvent.query.filter(WearEvent.user_id == session['user_id']).order_by(WearEvent.date.desc()).all()
    events = WearEvent.query.filter(WearEvent.user_id == session['user_id']).order_by(WearEvent.date).all()
    for event in events:
        month = event.date.month
        year = event.date.year
        evt_by_month[year] = evt_by_month.get(year, {})
        evt_by_month[year][month] = evt_by_month[year].get(month, [])
        evt_by_month[year][month].append(event)

    return render_template('events.html', evt_by_month=evt_by_month, MONTHS=MONTHS)


@app.route('/add-event')
def show_create_event_form():
    """Display form to create a new wear event/clothing log."""

    outfits = Outfit.query.filter(Outfit.user_id == session['user_id']).all()
    tags = Tag.query.filter(Tag.user_id == session['user_id']).all()

    return render_template('add-event.html',
                           CITIES=CITIES,
                           outfits=outfits,
                           tags=tags)


@app.route('/create-event', methods=['POST'])
def add_event():
    """Adds new event and redirects to the previous events page."""
    
    # String unpacking to pass as arguments to datetime
    year, month, day = request.form.get('event-date').split('-')
    time = request.form.get('event-time')
    city = request.form.get('city')
    description = request.form.get('event-description')
    name = request.form.get('event-name')
    outfit_id = request.form.get('event-outfit')
    tag_ids = request.form.getlist('event-tags')
    new_tag_string = request.form.get('new-tags')

    if time:
        hour, minute = time.split(':')
        date_time = datetime(int(year), int(month), int(day), int(hour), int(minute))
    else:
        date_time = datetime(int(year), int(month), int(day), int(10))

    # First create a new Event in the db
    event = WearEvent(user_id=session['user_id'],
                      outfit_id=outfit_id or None,
                      description=description or None,
                      name=name or f'{month}-{day}-{year}',
                      date=date_time)

    # If location is provided, get weather
    if city:
        event.set_weather(CITIES[city]['lat'], CITIES[city]['lng'])

    if outfit_id:
        outfit = Outfit.query.filter_by(outfit_id = outfit_id).one()
        outfit.incr_times_worn()

    all_tags = []
    for tag_id in tag_ids:
        all_tags.append(Tag.query.filter_by(tag_id = tag_id).one())

    # Any newly created tags should be added to this as well
    all_tags += Tag.parse_str_to_tag(new_tag_string, session['user_id'])

    # Then create all the tag relationships
    for tag in all_tags:
        event.add_tag(tag)

    db.session.add(event)
    db.session.commit()

    text = name if name else description

    flash(f"Created new outfit: {text}")

    return redirect('/events')


@app.route('/update-event', methods=['POST'])
def update_event_details():
    """Update an event's details."""
    
    event_id = request.form.get('event-to-edit')
    event = WearEvent.query.filter_by(wear_event_id = event_id).one()
    outfit_id = request.form.get('event-outfit')

    options = {}

    # TODO: this feels yucky
    name = request.form.get('update-name')
    description = request.form.get('update-description')
    tags = request.form.getlist('update-tags')
    if name:
        options['name'] = name
    if description:
        options['description'] = description
    for tag_id in tags:
        tag = Tag.query.filter_by(tag_id = tag_id).one()
        event.add_tag(tag)
    if outfit_id:
        options['outfit_id'] = outfit_id
        outfit = Outfit.query.filter_by(outfit_id = outfit_id).one()
        outfit.incr_times_worn()

    event.update(options)
    db.session.commit()

    return redirect(f'/events/{event_id}')


@app.route('/events/<wear_event_id>')
def show_event_details(wear_event_id):
    """Display specific event details."""

    event = WearEvent.query.filter_by(wear_event_id = wear_event_id).first()
    tags = Tag.query.filter_by(user_id = session['user_id']).all()
    outfits = Outfit.query.filter_by(user_id = session['user_id']).all()

    return render_template('single-event.html',
                           event=event,
                           tags=tags,
                           outfits=outfits)


@app.route('/delete-event', methods=['POST'])
def delete_event():
    """Deletes an event."""

    wear_event_id = request.form.get('event-to-delete')
    event = WearEvent.query.filter_by(wear_event_id = wear_event_id).one()

    event.delete()

    return redirect('/events')


@app.route('/etsy-api')
def test_etsy_api():
    """Test some Etsy API calls."""

    json_listings = etsy_api.getInterestingListings()

    return render_template('api-test.html', json_listings=json_listings)


@app.route('/weather/<city>')
def test_weather(city):
    """Test OpenWeatherMap's API & PyOWM wrapper"""

    # city = 'San Francisco'
    city_country = city + ',USA'
    print(city_country)
    observation = owm.three_hours_forecast(city_country)
    f = observation.get_forecast()
    forecasts = f.get_weathers()
    print(datetime.time(datetime.now()))
    for forecast in forecasts:
        forecast.temp = int(round(forecast.get_temperature('fahrenheit')['temp'],0))
        forecast.datestr = datetime.utcfromtimestamp(forecast.get_reference_time()).strftime('%H:%M')
    today = forecasts[0:8]

    return render_template('weather.html', today=today)


@app.route('/ds-weather')
def test_weather_darksky():
    """Test DarkSky's API & DarkSkyLib wrapper"""

    city = CITIES['SFO']
    # Dark Sky requires a date in isoformat
    weather = forecast(dark_sky['secret'], city['lat'], city['lng'])

    hourly = weather.hourly

    print(datetime.time(datetime.now()))
    for hour in hourly:

        hour.datestr = datetime.utcfromtimestamp(hour['time']).strftime('%m-%d-%y %H:%M')

    # for forecast in forecasts:
    #     forecast.temp = int(round(forecast.get_temperature('fahrenheit')['temp'],0))
    #     forecast.datestr = datetime.utcfromtimestamp(forecast.get_reference_time()).strftime('%H:%M')
    # today = forecasts[0:8]

    return render_template('ds-weather.html', hourly=hourly)


# # WIP - do some simpler steps first
# @app.route('/select-article/<outfit_id>/<category_id>/<article_id>')
# def add_or_replace_article_in_outfit(outfit_id, category_id, article_id):
#     """If category already in outfit, replace article in outfit; otherwise, add."""

#     outfit = Outfit.query.filter_by(outfit_id = outfit_id).one()
#     category = Category.query.filter_by(category_id = category_id).one()

#     if is_category_in_outfit(outfit, category):
#         pass
#     else:
#         pass

#     # outfit_categories = Category.query.filter(Outfit.articles.category_id == category_id).all()
#     # outfit = Outfit.query.filter(Outfit.outfit_id == outfit_id).one()

#     # categories = Category.query.filter(Category.user_id == session['user_id']).all()
#     # if category_id in outfit_categories:
#     #     outfit.article_id = article_id
#     # else:
#     #     outfit.article_id = article_id

#     return redirect(f'outfits/{outfit_id}',
#                     outfit=outfit,
#                     categories=categories)

# def update_article(article_id, outfit_id):
#     """Change article in outfit's category."""

#     article_outfit = ArticleOutfit.query.filter(ArticleOutfit.article_id == article_id,
#                                                 ArticleOutfit.outfit_id == outfit_id
#                                                 ).first()
    


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
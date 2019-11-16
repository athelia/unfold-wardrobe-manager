"""Web app for wardrobe management"""

from jinja2 import StrictUndefined
from flask import Flask, render_template, redirect, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.utils import secure_filename

import os
import requests
from datetime import datetime
from sqlalchemy import asc, update

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

# Compare clothing prices
from etsy import Etsy

# Get weather from OpenWeatherMap API
import pyowm

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


# TODO: consistent single quotes in render_template template names
@app.route('/')
def index():
    """If logged in, display homepage to go to outfits, categories, or articles."""
    if session.get('user_id', None):
        f = owm.three_hours_forecast(city_country).get_forecast()
        forecasts = f.get_weathers()
        print(datetime.time(datetime.now()))
        for forecast in forecasts:
            forecast.temp = int(round(forecast.get_temperature('fahrenheit')['temp'],0))
            forecast.datestr = datetime.utcfromtimestamp(forecast.get_reference_time()).strftime('%H:%M')
        today = forecasts[0:8]
        return render_template("homepage.html", today=today)
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


# WIP 
@app.route('/create-account')
def create_account_page():
    """Display account creation form."""

    return render_template("new-account.html")


@app.route('/categories')
def show_categories():
    """Display all user categories and the option to add a new category."""

    categories = Category.query.filter(Category.user_id == session['user_id']).all()

    return render_template("categories.html", 
                           categories=categories)


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

    new_category = Category(user_id=session['user_id'],
                            base_category_id=base_category,
                            name=name,
                            description=description)

    db.session.add(new_category)
    db.session.commit()

    flash(f"Created {new_category.name} successfully")

    return redirect('/categories')


@app.route('/articles')
def show_articles():
    """Display all articles of clothing and the option to add a new article."""

    articles = Article.query.filter(Article.user_id == session['user_id']).all()

    return render_template("articles.html", 
                           articles=articles)

@app.route('/add-article')
def show_create_article_form():
    """Display form to create a new article of clothing."""

    categories = Category.query.filter(Category.user_id == session['user_id']).all()

    return render_template("add-article.html",
                           categories=categories)


@app.route('/create-article', methods=['POST'])
def add_article():
    """Adds new clothing article and redirects to the previous category page."""

    category_id = request.form.get('category')
    description = request.form.get('article-description')
    file = request.files['article-image-upload']

    category = Category.query.filter_by(category_id=category_id).one()
    
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

        # Create a new Article in the database
        new_article = Article(user_id=session['user_id'],
                              category_id=category_id,
                              image=upload_file['secure_url'],
                              description=description)
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

    return render_template("single-article.html", 
                           article=article)


@app.route('/update-article', methods=['POST'])
def update_article_details():
    """Updates an article's details."""

    new_price = request.form.get('purchase-price')
    article_id = request.form.get('article-to-edit')
    article = Article.query.filter_by(article_id = article_id).one()

    article.update({'purchase_price' : new_price})
    return redirect(f'/articles/{article_id}')


@app.route('/outfits')
def show_outfits():
    """Display all outfits and the option to add a new outfit."""

    outfits = Outfit.query.filter(Outfit.user_id == session['user_id']).all()

    return render_template('outfits.html', outfits=outfits)


@app.route('/add-outfit')
def show_create_outfit_form():
    """Display form to create a new outfit."""

    categories = Category.query.filter(Category.user_id == session['user_id']).all()

    return render_template('add-outfit.html', categories=categories)


@app.route('/create-outfit', methods=['POST'])
def add_outfit():
    """Adds new outfit and redirects to the previous outfits page."""

    description = request.form.get('outfit-description')
    name = request.form.get('outfit-name')
    article_ids = request.form.getlist('articles-to-add')

    # First create a new Outfit in the db
    outfit = Outfit(user_id=session['user_id'],
                    description=description,
                    name=name)
    db.session.add(outfit)
    db.session.commit()

    # Then create all the article relationships
    for article_id in article_ids:
        article = Article.query.filter(Article.article_id == article_id).one()
        outfit.add_article(article)
        db.session.commit()

    text = name if name else description

    flash(f"Created new outfit: {text}")

    return redirect('/outfits')


@app.route('/outfits/<outfit_id>')
def show_outfit_detail(outfit_id):
    """Display specific outfit details."""

    outfit = Outfit.query.filter_by(outfit_id = outfit_id).first()
    categories = Category.query.filter(Category.user_id == session['user_id']).all()

    return render_template('single-outfit.html',
                           outfit=outfit,
                           categories=categories)


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


@app.route('/etsy-api')
def test_etsy_api():
    """Test some Etsy API calls."""

    json_listings = etsy_api.getInterestingListings()

    return render_template('api-test.html', json_listings=json_listings)


@app.route('/profile')
def show_profile():
    """Display logged-in user's profile."""

    if session.get('user_id'):
        user = User.query.filter_by(user_id = session['user_id']).one()
    else:
        user = None

    return render_template('profile.html', user=user)


# @app.route('/update-outfit')
# def add_article_to_outfit():
#     """Adds an article to the current outfit."""

#     # I can figure out how to send the article and outfit via a "get req"
#     # within the link, but how do I send it with a post req and no
#     # form? 
#     outfit.add_article(article)

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
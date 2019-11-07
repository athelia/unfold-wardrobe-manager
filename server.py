"""Web app for wardrobe management"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension

from werkzeug.utils import secure_filename

import os

from sqlalchemy import asc, update

from flask_login import LoginManager

# Import helper function, SQLAlchemy database, and model definitions
from model import (connect_to_db, db, User, BaseCategory, Category, Article,
    Outfit, Tag, ArticleOutfit, TagArticle, TagOutfit)

# Import functions for image storage and processing
from image_handling import allowed_file, ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config.from_pyfile('flaskconfig.cfg')

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined

# UPLOAD_FOLDER = '/var/www/uploads'
# ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
# Flask-Login is WIP
# # Flask-Login needs some setup
# login_manager = LoginManager()
# login_manager.init_app(app)


# Flask-Login is WIP
# AttributeError: type object 'User' has no attribute 'get'
# @login_manager.user_loader
# def load_user(user_id):
#     return User.get(user_id)


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


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
        return redirect('/categories')
    else:
        flash("Invalid email & password combination. Please try again.")
        return redirect('/')


@app.route('/categories')
def show_categories():
    """Display all user categories and the option to add a new category."""

    categories = Category.query.filter(User.user_id == session['user_id']).all()

    return render_template("categories.html", 
                           categories=categories)


@app.route('/categories/<category_id>')
def show_category_articles(category_id):
    """Display articles of clothing belonging to selected category."""

    articles = Article.query.filter(Article.category_id == category_id,
                                    User.user_id == session['user_id']).all()
    category = Category.query.filter(Category.category_id == category_id,
                                     User.user_id == session['user_id']).one()

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


@app.route('/add-article')
def show_create_article_form():
    """Display form to create a new article of clothing."""

    categories = Category.query.filter(User.user_id == session['user_id']).all()

    return render_template("add-article.html",
                           categories=categories)


# def allowed_file(filename):
#     # print(filename.rsplit('.',1)[1].lower())
#     return ('.' in filename and 
#         filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS)


@app.route('/create-article', methods=['POST'])
def add_article():
    """Adds new clothing article and redirects to the previous category page."""

    category_id = request.form.get('category')
    description = request.form.get('article-description')
    file = request.files['article-image-upload']
    
    # print(f'\n\n\n\nFilename: {file.filename}\nExtension:{file.filename.rsplit(".",1)[1].lower()}\n\n\n\n')
    if not allowed_file(file.filename):
        flash(f'File extension .{file.filename.rsplit(".", 1)[1]} not allowed')
    if file and allowed_file(file.filename):
        # Sanitizes user input to prevent malicious injection
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], str(session['user_id']))
        
        if not os.path.exists(path):
            os.makedirs(path)
        
        img_src = file.save(os.path.join(path), filename)
        new_article = Article(user_id=session['user_id'],
                              category_id=category_id,
                              img=img_src,
                              description=description)
        db.session.add(new_article)
        db.session.commit()
        flash(f"Created new item in {new_article.categories.name}")

    return redirect(f'/categories/{category_id}')


@app.route('/articles/<article_id>')
def show_article_detail(article_id):
    """Display specific article details."""

    # articles = Article.query.filter(Article.category_id==category.category_id, User.user_id==session['user_id']).all()

    # return render_template("articles.html", 
    #                        articles=articles)
    pass


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
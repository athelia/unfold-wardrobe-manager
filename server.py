"""Web app for wardrobe management"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension

# Import helper function, SQLAlchemy database, and model definitions
from model import (connect_to_db, db, User, BaseCategory, Category, Article,
    Outfit, Tag, ArticleOutfit, TagArticle, TagOutfit)

from sqlalchemy import asc, update


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined

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
    user = User.query.filter(User.email==email, User.password==password).first()

    if user:
        # Add user's id and email to session
        session['user_id'] = user.user_id
        session['user_email'] = user.email
        flash(f"Welcome back, {session['user_email']}!")
        return redirect('/categories')
    else:
        flash("Invalid email & password combination. Please try again.")
        return redirect('/')


@app.route('/categories')
def show_categories():
    """Display all user categories and the option to add a new category."""

    categories = Category.query.all()

    return render_template("categories.html", 
                           categories=categories)


@app.route('/categories/<category_id>')
def show_articles(category_id):
    """Display articles of clothing belonging to selected category."""

    articles = Article.query.filter(Article.category_id==category_id).all()
    category = Category.query.filter(Category.category_id==category_id).one()

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

    categories = Category.query.all()

    return render_template("add-article.html",
                           categories=categories)


@app.route('/create-article', methods=['POST'])
def add_article():
    """Adds new clothing article and redirects to the previous category page."""

    name = request.form.get('category-name')
    category_id = request.form.get('category')
    description = request.form.get('category-description')

    new_article = Article(user_id=session['user_id'],
                          category_id=category_id,
                          description=description)
    db.session.add(new_article)
    db.session.commit()

    flash(f"Created {new_article.name} successfully")

    return redirect(f'/categories/{category_id}')


@app.route('/articles/<article_id>')
def show_article_detail(article_id):
    """Display specific article details."""

    # articles = Article.query.filter(Article.category_id==category.category_id).all()

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
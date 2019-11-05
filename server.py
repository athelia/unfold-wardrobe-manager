"""Web app for wardrobe management"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension

# Import helper function, SQLAlchemy database, and model definitions
from model import (connect_to_db, db, User, BaseCategory, UserCategory, Article,
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
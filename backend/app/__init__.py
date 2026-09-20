import os

from flask import Flask
from dotenv import load_dotenv

from .extensions import db, migrate


load_dotenv()


def create_app():

    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    migrate.init_app(app, db)

    from . import models

    return app
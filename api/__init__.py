import datetime
import logging
from logging.handlers import RotatingFileHandler

from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, request
from raven.contrib.flask import Sentry

import config

app = Flask(__name__)
app.config.from_object("api.config")
login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app)

file_handler = RotatingFileHandler("/var/log/api.log")
file_handler.setLevel(logging.WARNING)
app.logger.addHandler(file_handler)

try:
    from sentry_dsn import dsn
    app.config['SENTRY_DSN'] = dsn
    sentry = Sentry(app)
except: ImportError

import views.views, models

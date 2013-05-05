from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from raven.contrib.flask import Sentry

from flask.ext.login import LoginManager

LF_API_URL = "http://ws.audioscrobbler.com/2.0/?"
LF_API_KEY = "7caf7bfb662c58f659df4446c7200f3c&"
SP_API_URL = "http://ws.spotify.com"
FB_API_URL = "https://graph.facebook.com"
DATABASE_FILE = '/tmp/queue.db'
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % DATABASE_FILE
SECRET_KEY = "yeah, not actually a secret"
login_manager = LoginManager()

app = Flask(__name__)
app.config.from_object(__name__)
login_manager.init_app(app)
db = SQLAlchemy(app)

import models

try:
    from sentry_dsn import dsn
    app.config['SENTRY_DSN'] = dsn
    sentry = Sentry(app)
except: ImportError




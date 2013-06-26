import datetime
from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from raven.contrib.flask import Sentry

from flask.ext.login import LoginManager

LF_API_URL = "http://ws.audioscrobbler.com/2.0/?"
LF_API_KEY = "7caf7bfb662c58f659df4446c7200f3c&"
TS_API_KEY = "6b08a682cc42b6eda827a1d1a9ab838a"
TS_API_URL =  "http://tinysong.com"
SP_API_URL = "http://ws.spotify.com"
FB_API_URL = "https://graph.facebook.com"
DATABASE_FILE = 'queue.db'
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % DATABASE_FILE
SECRET_KEY = "yeah, not actually a secret"
PERMANENT_SESSION_LIFETIME = datetime.timedelta(minutes=525949)
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




from flask import Flask, request
from flask.ext.restful import Resource, Api, reqparse
from flask.ext.sqlalchemy import SQLAlchemy
from raven.contrib.flask import Sentry

LF_API_URL = "http://ws.audioscrobbler.com/2.0/?"
LF_API_KEY = "7caf7bfb662c58f659df4446c7200f3c&"
SP_API_URL = "http://ws.spotify.com"
FB_API_URL = "https://graph.facebook.com"
DATABASE_FILE = '/tmp/queue.db'
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % DATABASE_FILE

app = Flask(__name__)
app.config.from_object(__name__)
sentry = Sentry(app, dsn='http://localhost:9000')
api = Api(app)
db = SQLAlchemy(app)

import models
#if not app.debug:
#    import logging
#    from logging import FileHandler
#    file_handler = FileHandler('/tmp/queue.log')
#    file_handler.setLevel(logging.WARNING)
#    from logging import Formatter
#    file_handler.setFormatter(Formatter(
#    '%(asctime)s %(levelname)s: %(message)s '
#    '[in %(pathname)s:%(lineno)d]'
#    ))
#    app.logger.addHandler(file_handler)

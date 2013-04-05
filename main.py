from flask import Flask, request
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
app.config['SENTRY_DSN'] = 'http://ba87f6268ed54183bea4b3ff4ee3a86f:45974bce87574e0ba5fae80e3a48644a@198.199.67.210:9000/2'
sentry = Sentry(app)
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

import os
import datetime

from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, request
from raven.contrib.flask import Sentry

app = Flask(__name__)

if os.environ['QUEUE_API_MODE'] == 'TEST':
    app.config.from_object("api.test_config")
else:
    app.config.from_object("api.prod_config")

login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app)

app.logger.addHandler(app.config["LOG_HANDLER"])

# sentry = Sentry(app.config['SENTRY_DSN'])

import views.views, models

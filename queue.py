from flask import Flask, request
from flask.ext.restful import Resource, Api, reqparse
from flask.ext.sqlalchemy import SQLAlchemy


API_URL = "http://ws.audioscrobbler.com/2.0/?"
API_KEY = "7caf7bfb662c58f659df4446c7200f3c&"
DATABASE_FILE = '/tmp/queue.db'
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % DATABASE_FILE

app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)
db = SQLAlchemy(app)

import models


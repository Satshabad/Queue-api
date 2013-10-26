import datetime
import logging
from logging.handlers import RotatingFileHandler


DATABASE_FILE = '/srv/www/queue/api/queue.db'
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(DATABASE_FILE)
SECRET_KEY = "yeah, not actually a secret"
PERMANENT_SESSION_LIFETIME = datetime.timedelta(minutes=525949)
file_handler = RotatingFileHandler("/var/log/api.log")
file_handler.setLevel(logging.WARNING)
LOG_HANDLER = file_handler


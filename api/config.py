import datetime

DATABASE_FILE = '/srv/www/queue/api/queue.db'
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(DATABASE_FILE)
SECRET_KEY = "yeah, not actually a secret"
PERMANENT_SESSION_LIFETIME = datetime.timedelta(minutes=525949)

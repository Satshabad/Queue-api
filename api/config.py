import datetime

FB_API_URL = "https://graph.facebook.com"
DATABASE_FILE = '/srv/www/queue/api/queue.db'
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % DATABASE_FILE
SECRET_KEY = "yeah, not actually a secret"
PERMANENT_SESSION_LIFETIME = datetime.timedelta(minutes=525949)

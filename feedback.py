import os

from apnsclient import Session, APNs 
from models import User
from app import db

def remove_tokens():
# feedback needs no persistent connections.
    con = Session.new_connection(("gateway.push.apple.com", 2196), cert_file=os.path.join(os.getcwd(), 'cert.pem'), passphrase="this is the queue push key")

# feedback server might be slow, so allow it to time out in 10 seconds
    srv = APNs(con, tail_timeout=10)

# automatically closes connection for you
    for token, since in srv.feedback():
        user = db.session.query(User).filter(User.device_token == token).one()
        user.device_token = None
        db.session.add(user)

    db.session.commit()

if __name__ == "__main__":
    remove_tokens()

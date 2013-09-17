from flask import jsonify
from flask.ext.login import current_user

from api import app, db, login_manager
from api.lib import facebook
from api.models import User


class APIException(Exception):

    def __init__(self, message, status_code):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        rv = {}
        rv['message'] = self.message
        return rv


def make_message(message):
    return jsonify({'message': message})


def get_user(user_id, by_fb_id=False):
    if by_fb_id:
        user_matches = db.session.query(User).filter(User.fb_id == user_id)

        if not list(user_matches):
            return None

        return user_matches[0]

    return db.session.query(User).get(user_id)


def get_user_or_404(user_id, by_fb_id=False):
    user = get_user(user_id, by_fb_id)

    if user is None:
        raise APIException("user not found", 404)

    return user


def assert_user_is_unclaimed(user):
    if user.claimed == True:
        raise APIException("you don't have permission to do that", 403)


def assert_is_current_user(user):
    if user != current_user:
        raise APIException("you don't have permission to do that", 403)


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@login_manager.user_loader
def load_user(userid):
    return db.session.query(User).get(userid)


def assert_are_friends(user_id_1, user_id_2, access_token):
    if user_id_1 == user_id_2:
        return

    if not facebook.are_friends(user_id_1, user_id_2, access_token):
        raise APIException("users are not friends", 403)

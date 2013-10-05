import calendar
import datetime

from flask import request, jsonify, session
from flask.ext.login import (login_required,
                             login_user,
                             logout_user)

from api import app, db
from api.lib import twit, lastfm, facebook, push
from api.models import marshall

from api.views.base import (make_message,
                            assert_user_is_unclaimed,
                            get_user_or_404,
                            APIException,
                            get_user,
                            assert_are_friends,
                            assert_is_current_user)

from api.models import (SongItem,
                        User,
                        Artist,
                        Album,
                        Friend,
                        ArtistItem,
                        NoteItem,
                        UrlsForItem,
                        QueueItem)

DEFAULT_SIZE = 20


@app.route('/', methods=['GET'])
def home():
    raise APIException("nothing to see here, move along", 200)


@app.route('/login', methods=['POST'])
def login():
    params = request.json
    access_token = params.get('accessToken')
    fb_id = params['fbId']

    user = get_user(fb_id, by_fb_id=True)

    if user is None:
        if access_token is None:
            raise APIException('please provide accessToken', 400)
        else:

            if not facebook.verify(fb_id, access_token):
                raise APIException("access token invalid", 403)

            user = User(fb_id=fb_id, access_token=access_token,
                        fullname=params['fullName'],
                        image_link=params['imageLink'],
                        badge_setting=params.get('badgeSetting'),
                        device_token=params.get('deviceToken'),
                        badge_num=0,
                        claimed=True)

            db.session.add(user)
            db.session.commit()
    else:
        if access_token is None:
            assert_user_is_unclaimed(user)
        else:
            if not facebook.verify(fb_id, access_token):
                raise APIException("access token invalid", 403)
            if user.claimed == False:
                user.claimed = True
                db.session.add(user)
                db.session.commit()

    if login_user(user, remember=True):
        session.permanent = True
        return jsonify(user.dictify())

    # Why would this happen?
    raise APIException('could not log in', 400)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return make_message("logged out")


@app.route('/user/<user_id>', methods=['PUT'])
@login_required
def change_user(user_id):
    params = request.json
    lastfm_name = params.get('lastFMUsername', None)
    twitter_name = params.get('twitterUsername', None)
    device_token = params.get('deviceToken', None)
    badge_setting = params.get('badgeSetting', None)

    user = get_user_or_404(user_id)
    assert_is_current_user(user)

    if lastfm_name is not None:
        user.lastfm_name = lastfm_name

    if twitter_name is not None:
        user.twitter_name = twitter_name

    if device_token is not None:
        user.device_token = device_token

    if badge_setting is not None:
        user.badge_setting = badge_setting
        recalc_badge_num(user.id)

    db.session.add(user)
    db.session.commit()
    return jsonify(user.dictify())


@app.route('/user/<user_id>/queue', methods=['GET'])
def get_queue(user_id):
    page = int(request.args.get('page') or 1)

    user = get_user_or_404(user_id)

    items = QueueItem.query.filter(
        QueueItem.user_id == user.id).filter(
        QueueItem.listened == 0).order_by(
        QueueItem.date_queued.desc()).paginate(
        page, error_out=False).items

    queue = []
    for item in items:
        queue.append(item.dictify())

    return jsonify({'queue': {'items': list(queue)}})


@app.route('/user/<user_id>/queue/<item_id>', methods=['DELETE'])
@login_required
def delete_queue_item(user_id, item_id):
    user = get_user_or_404(user_id)
    assert_is_current_user(user)

    queue_item = QueueItem.query.get(item_id)

    if queue_item is None:
        raise APIException("queue item not found", 404)

    assert_is_current_user(queue_item.user)

    was_shared = queue_item.queued_by_id != queue_item.user_id
    was_listened = queue_item.listened

    item_type, item = queue_item.get_item()
    db.session.delete(item)
    db.session.delete(queue_item)

    if user.badge_setting == "unlistened":
        if not was_listened:
            user.badge_num -= 1

            push.change_badge_number(user)

    db.session.add(user)
    db.session.commit()
    return make_message("item deleted")


@app.route('/user/<user_id>/queue/<item_id>', methods=['PUT', 'POST'])
@login_required
def change_queue_item(user_id, item_id):
    listened = True if request.json['saved'] == 1 else False

    user = get_user_or_404(user_id)
    assert_is_current_user(user)

    item = QueueItem.query.get(item_id)

    if item is None:
        raise APIException("item not found", 404)

    assert_is_current_user(item.user)

    was_listened = item.listened
    was_shared = item.queued_by_id != item.user_id
    item.listened = listened
    db.session.add(item)

    if user.badge_setting == "unlistened":
        if listened and not was_listened:
            user.badge_num -= 1

        if not listened and was_listened:
            user.badge_num += 1

        push.change_badge_number(user)

    db.session.add(user)

    db.session.commit()

    return jsonify(item.dictify())


@app.route('/fbuser/<fb_id>/queue', methods=['POST'])
@login_required
def enqueue_item_by_fbid(fb_id):
    params = request.json
    from_user_id = params['fromUser']['userID']
    access_token = params['fromUser']['accessToken']

    from_user = get_user_or_404(from_user_id)
    to_user = get_user(fb_id, by_fb_id=True)

    assert_are_friends(from_user.fb_id, fb_id, access_token)

    if to_user is None:
        # TODO: maybe get some info here
        to_user = User(fb_id=fb_id, access_token=None,
                       fullname="",
                       image_link="",
                       badge_setting=None,
                       device_token=None,
                       badge_num=0,
                       claimed=False)

        db.session.add(to_user)
        db.session.commit()

    assert_is_current_user(from_user)

    return enqueue_item(to_user.id)


@app.route('/user/<user_id>/queue', methods=['POST'])
@login_required
def enqueue_item(user_id):

    params = request.json
    from_user_id = params['fromUser']['userID']
    access_token = params['fromUser']['accessToken']
    item_data = params[params['type']]

    from_user = get_user_or_404(from_user_id)
    to_user = get_user_or_404(user_id)

    assert_is_current_user(from_user)

    assert_are_friends(from_user.fb_id, to_user.fb_id, access_token)

    orm_queue_item = QueueItem(user=to_user, queued_by_user=from_user,
                               urls=None,
                               listened=False,
                               date_queued=calendar.timegm(datetime.datetime.utcnow().utctimetuple()))
    if 'song' in params:
        orm_song = marshall.create_song(item_data)
        orm_urls = marshall.make_urls_for_song(item_data)

        orm_queue_item.urls = orm_urls
        orm_queue_item.song_item = [orm_song]

    elif 'artist' in params:
        orm_artist = marshall.make_artist_model(item_data)
        orm_urls = marshall.make_urls_for_artist(item_data)

        orm_queue_item.urls = orm_urls
        orm_queue_item.artist_item = [orm_artist]

    elif 'note' in params:
        orm_note = marshall.make_note_model(item_data)
        orm_urls = marshall.make_urls_for_note(item_data)

        orm_queue_item.urls = orm_urls
        orm_queue_item.note_item = [orm_note]

    db.session.add(orm_queue_item)

    if from_user.id != to_user.id:

        if to_user.badge_setting == "unlistened":
            to_user.badge_num += 1
            push.alert_and_change_badge_number(
                from_user, to_user, params['type'])

    else:
        if to_user.badge_setting == "unlistened":
            to_user.badge_num += 1

            push.change_badge_number(to_user)

    db.session.add(to_user)
    db.session.commit()

    return jsonify(orm_queue_item.dictify())


@app.route('/user/<user_id>/sent', methods=['GET'])
def get_sent(user_id):
    page = int(request.args.get('page') or 1)
    size = int(request.args.get('size') or DEFAULT_SIZE)
    user = get_user_or_404(user_id)

    items = QueueItem.query.filter(
        QueueItem.queued_by_id == user.id).filter(
        QueueItem.user_id != user.id).order_by(
        QueueItem.date_queued.desc()).paginate(
        page, per_page=size, error_out=False).items

    queue = []
    for item in items:
        queue.append(item.dictify())

    return jsonify({'queue': {'items': list(queue)}})


@app.route('/user/<user_id>/saved', methods=['GET'])
def get_saved(user_id):
    page = int(request.args.get('page') or 1)
    user = get_user_or_404(user_id)

    items = QueueItem.query.filter(
        QueueItem.user_id == user.id).filter(
        QueueItem.listened).order_by(
        QueueItem.date_queued.desc()).paginate(page, error_out=False).items

    queue = []
    for item in items:
        queue.append(item.dictify())

    return jsonify({'queue': {'items': list(queue)}})


@app.route('/user/<user_id>/saved/<item_id>', methods=['DELETE'])
@login_required
def delete_queue_item(user_id, item_id):
    user = get_user_or_404(user_id)
    assert_is_current_user(user)

    queue_item = QueueItem.query.get(item_id)

    if queue_item is None:
        raise APIException("saved item not found", 404)

    assert_is_current_user(queue_item.user)

    item_type, item = queue_item.get_item()
    db.session.delete(item)
    db.session.delete(queue_item)

    db.session.commit()
    return make_message("item deleted")


@app.route('/user/<user_id>/listens', methods=['GET'])
def get_listens(user_id):
    user = get_user_or_404(user_id)

    listens = []
    if user.lastfm_name:
        listens.extend(lastfm.get_user_listens(user.lastfm_name))
    if user.twitter_name:
        listens.extend(twit.get_user_listens(user.twitter_name))

    data = {
        'recentTracks': {
            'tracks': sorted(
                listens,
                lambda k1,
                k2: k1[
                    'dateListened'] > k2[
                    'dateListened'])}}

    return jsonify(data)


@app.route('/search/<search_text>', methods=['GET'])
def search(search_text):
    tracks = lastfm.search_for_songs(search_text)[:5]
    artists = lastfm.search_for_artists(search_text)[:5]
    results = {'trackResults': tracks, 'artistResults': artists}

    return jsonify(results)


def recalc_badge_num(user_id):
    user = User.query.get(user_id)
    user_items = QueueItem.query.filter(
        QueueItem.user_id == user.id)

    if user.badge_setting == "unlistened":
        user.badge_num = sum(map(lambda x: 0 if x.listened else 1, user_items))

    if user.badge_setting is None:
        user.badge_num = 0

    db.session.add(user)
    db.session.commit()

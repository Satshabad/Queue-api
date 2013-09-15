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


@app.route('/', methods=['GET'])
def home():
    raise APIException("nothing to see here, move along", 200)


@app.route('/login', methods=['POST'])
def login():
    args = request.json
    access_token = args['accessToken']
    fb_id = args['fbId']

    if not facebook.verify(fb_id, access_token):
        raise APIException("access token invalid", 400)

    user = get_user(fb_id, by_fb_id=True)

    if not user:
        user = User(fb_id=fb_id, access_token=access_token,
                    fullname=args['fullName'],
                    image_link=args['imageLink'],
                    badge_setting=args.get('badgeSetting'),
                    device_token=args.get('deviceToken'),
                    badge_num=0)

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
    args = request.json
    lastfm_name = args.get('lastFMUsername', None)
    twitter_name = args.get('twitterUsername', None)
    device_token = args.get('deviceToken', None)
    badge_setting = args.get('badgeSetting', None)

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

    user = get_user_or_404(user_id)

    items = db.session.query(QueueItem)\
        .filter(QueueItem.user_id == user.id).all()

    queue = []
    for item in items:
        queue.append(item.dictify())

    return jsonify({'queue': {'items': list(reversed(queue))}})


@app.route('/user/<user_id>/queue/<item_id>', methods=['DELETE'])
@login_required
def delete_queue_item(user_id, item_id):
    user = get_user_or_404(user_id)

    assert_is_current_user(user)

    queue_item = db.session.query(QueueItem).get(item_id)

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

            push.notify(user.device_token, badge_num=user.badge_num)

    if user.badge_setting == "shared":
        if not was_listened and was_shared:
            user.badge_num -= 1

            push.notify(user.device_token, badge_num=user.badge_num)

    db.session.add(user)
    db.session.commit()
    return make_message("item deleted")


@app.route('/user/<user_id>/queue/<item_id>', methods=['PUT'])
@login_required
def change_queue_item(user_id, item_id):
    listened = True if request.json['saved'] == 1 else False

    user = get_user_or_404(user_id)

    assert_is_current_user(user)

    item = db.session.query(QueueItem).get(item_id)

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
            push.notify(user.device_token, badge_num=user.badge_num)

        if not listened and was_listened:
            user.badge_num += 1
            push.notify(user.device_token, badge_num=user.badge_num)

    if user.badge_setting == "shared":
        if was_shared:
            if listened and not was_listened:
                user.badge_num -= 1
                push.notify(user.device_token, badge_num=user.badge_num)

            if not listened and was_listened:
                user.badge_num += 1
                push.notify(user.device_token, badge_num=user.badge_num)

    db.session.add(user)

    db.session.commit()

    return jsonify(item.dictify())


@app.route('/fbuser/<fb_id>/queue', methods=['POST'])
@login_required
def enqueue_item_by_fbid(fb_id):
    queue_item = request.json
    from_user_id = queue_item['fromUser']['userID']

    from_user = get_user_or_404(from_user_id)
    to_user = get_user_or_404(fb_id, by_fb_id=True)

    assert_is_current_user(from_user)

    return enqueue_item(to_user.id)


@app.route('/user/<user_id>/queue', methods=['POST'])
@login_required
def enqueue_item(user_id):

    post_data = request.json
    from_user_id = post_data['fromUser']['userID']
    access_token = post_data['fromUser']['accessToken']
    item_data = post_data[post_data['type']]

    from_user = get_user_or_404(from_user_id)
    to_user = get_user_or_404(user_id)

    assert_is_current_user(from_user)

    assert_are_friends(from_user.fb_id, to_user.fb_id, access_token)

    orm_queue_item = QueueItem(user=to_user, queued_by_user=from_user,
                               urls=None,
                               listened=False,
                               date_queued=calendar.timegm(datetime.datetime.utcnow().utctimetuple()))
    if 'song' in post_data:
        orm_song = marshall.create_song(item_data)
        orm_urls = marshall.make_urls_for_song(item_data)

        orm_queue_item.urls = orm_urls
        orm_queue_item.song_item = [orm_song]

    elif 'artist' in post_data:
        orm_artist = marshall.make_artist_model(item_data)
        orm_urls = marshall.make_urls_for_artist(item_data)

        orm_queue_item.urls = orm_urls
        orm_queue_item.artist_item = [orm_artist]

    elif 'note' in post_data:
        orm_note = marshall.make_note_model(item_data)
        orm_urls = marshall.make_urls_for_note(item_data)

        orm_queue_item.urls = orm_urls
        orm_queue_item.note_item = [orm_note]

    db.session.add(orm_queue_item)

    if from_user.id != to_user.id and to_user.device_token:
        if to_user.badge_setting == "shared":
            to_user.badge_num += 1
            push.notify(to_user.device_token,
                        message="%s shared a %s with you" % (
                            from_user.fullname, post_data['type']),
                        badge_num=to_user.badge_num,
                        name=from_user.fullname, item_type=post_data['type'])
        else:
            push.notify(to_user.device_token,
                        message="%s shared a %s with you" % (
                            from_user.fullname, post_data['type']),
                        name=from_user.fullname, item_type=post_data['type'])

    if from_user.id == to_user.id and to_user.badge_setting == "unlistened":
        to_user.badge_num += 1
        push.notify(to_user.device_token, badge_num=to_user.badge_num)

    db.session.add(to_user)
    db.session.commit()

    return jsonify(orm_queue_item.dictify())


@app.route('/user/<user_id>/sent', methods=['GET'])
def get_sent(user_id):
    user = get_user_or_404(user_id)

    items = db.session.query(QueueItem)\
        .filter(QueueItem.queued_by_id == user.id).all()

    queue = []
    for item in items:
        queue.append(item.dictify())

    return jsonify({'queue': {'items': list(reversed(queue))}})


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

    user = db.session.query(User).get(user_id)
    user_items = db.session.query(
        QueueItem).filter(
        QueueItem.user_id == user.id)

    if user.badge_setting == "unlistened":
        user.badge_num = sum(map(lambda x: 0 if x.listened else 1, user_items))

    if user.badge_setting == "shared":
        user.badge_num = sum(
            map(lambda x: 1 if not x.listened and x.queued_by_id != user.id else 0, user_items))

    if user.badge_setting is None:
        user.badge_num = 0

    db.session.add(user)
    db.session.commit()

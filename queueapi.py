import datetime
import json
import calendar
import os
from functools import wraps

from flask import Flask, request, jsonify
from flask import redirect, request, current_app

import requests

from main import app, db

from models import SongItem, User, Artist, Album, Friend, ArtistItem, NoteItem, UrlsForItem, QueueItem
from fixdata import fix_lastfm_listens_data, fix_image_data, fix_lf_track_search, fix_lf_artist_search, fix_search_metadata


SP_API_URL = app.config['SP_API_URL']
LF_API_URL = app.config['LF_API_URL']
LF_API_KEY = app.config['LF_API_KEY']
FB_API_URL = app.config['FB_API_URL']
 
def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f().data) + ')'
            return current_app.response_class(content, mimetype='application/json')
        else:
            return f(*args, **kwargs)
    return decorated_function

@app.route('/db/destroy')
def destroy_db():
    os.remove(app.config['DATABASE_FILE'])
    return 'so it is'


@app.route('/db/create')
def create_db():
    import init_db
    init_db.init_db()
    return 'so it is'

@app.route('/search/<search_text>', methods=['GET'])
@support_jsonp
def search(search_text):
    search_url = "%smethod=track.search&track=%s&api_key=%sformat=json"
    track_results = requests.get(search_url %
                    (LF_API_URL, search_text, LF_API_KEY)).json()['results']

    search_url = "%smethod=artist.search&artist=%s&api_key=%sformat=json"
    artist_results = requests.get(search_url %
                    (LF_API_URL, search_text, LF_API_KEY)).json()['results']

    results = {'track_results':fix_lf_track_search(track_results),
               'artist_results':fix_lf_artist_search(artist_results)}

    return jsonify(results)

@app.route('/<user_name>/listens', methods=['GET'])
@support_jsonp
def get_listens(user_name):
    data = requests.get("%smethod=user.getrecenttracks&user=%s&api_key=%sformat=json&extended=1"
                        % (LF_API_URL, user_name, LF_API_KEY)).json()
    return jsonify(fix_lastfm_listens_data(data))

@app.route('/', methods=['GET'])
@support_jsonp
def home():
    return jsonify({"hello":"there"})

@app.route('/<user_name>/friends', methods=['GET'])
@support_jsonp
def get_friends(user_name):
    args = request.values
    access_token = args['accessToken']
    user = get_user(user_name)

    if not user:
        return no_such_user(user_name)

    friends = []
    for friend in db.session.query(Friend).filter(Friend.user_id == user.id):
        friends.append(friend.dictify())

    return jsonify(friends)

@app.route('/<user_name>', methods=['POST'])
@support_jsonp
def make_user(user_name):

    if get_user(user_name):
       return {'message': 'user already exists'}, 400

    args = request.json
    access_token = args['accessToken']
    fb_id = args['fbId']
    friends = get_fb_friends(fb_id, access_token)

    if friends == None:
        return {"message": 'problem getting friends'}, 500

    user = User(fb_id=fb_id, uname=user_name, access_token=access_token,
                fullname=args['fullname'], image_link=args['imageLink'])
    for friend in friends:
        f = Friend(fullname=friend['name'], fb_id=friend['id'], user=user)
        db.session.add(f)

    db.session.add(user)
    db.session.commit()

    return jsonify({"status":"OK"})

@app.route('/<user_name>/queue', methods=['GET'])
@support_jsonp
def get_queue(user_name):

    user = get_user(user_name)

    if not user:
        return no_such_user(user_name)

    items = db.session.query(QueueItem)\
        .filter(QueueItem.user_id == user.id).all()
    
    queue = []
    for item in items:
        queue.append(item.dictify())

    queue = sorted(queue, key=lambda x: (x['listened'], -1*x['dateQueued']))
    return jsonify({"queue":{"items":queue}})

@app.route('/<user_name>/queue/<item_id>', methods=['DELETE'])
@support_jsonp
def delete_queue_item(user_name, item_id):
    access_token = request.values['accessToken']
    user = get_user(user_name)

    if not user.access_token == access_token:
        app.logger.warning("invalid accessTokenfor user %s" % user_name)
        return {'message':'invalid accessToken'}, 400

    queue_item = db.session.query(QueueItem)\
        .filter(QueueItem.user_id == user.id)\
        .filter(QueueItem.id == item_id).one()

    item_type, item = queue_item.get_item()
    db.session.delete(item)
    db.session.delete(queue_item)
    db.session.commit()

    return jsonify({'status': 'OK'})

@app.route('/<user_name>/queue/<item_id>', methods=['PUT'])
@support_jsonp
def mark_listened(user_name, item_id):
    access_token = request.values['accessToken']
    listened = True if request.values['listened'] == 'true' else False
    user = get_user(user_name)

    if not user.access_token == access_token:
        app.logger.warning("invalid accessTokenfor user %s" % user_name)
        return {'message':'invalid accessToken'}, 400

    item = db.session.query(QueueItem)\
        .filter(QueueItem.user_id == user.id)\
        .filter(QueueItem.id == item_id).one()

    item.listened = listened
    db.session.add(item)
    db.session.commit()

    return jsonify({'status': 'OK'})

@app.route('/<user_name>/queue', methods=['POST'])
@support_jsonp
def enqueue_item(user_name):

    queue_item = request.json
    from_user_name = queue_item['fromUser']['userName']
    access_token = queue_item['fromUser']['accessToken']
    media = queue_item[queue_item['type']]

    from_user = get_user(from_user_name)
    to_user = get_user(user_name)

    if not from_user:
        return no_such_user(from_user)

    if not to_user:
        return no_such_user(to_user)

    if not from_user.access_token == access_token:
        app.logger.warning("invalid accessTokenfor user %s" % user_name)
        return jsonify({'message':'invalid accessToken'}), 400

    if user_name != from_user_name and not is_friends(from_user, to_user):
        app.logger.warning("users %s is not friends" % user_name)
        return jsonify({'message':'users are not friends'}), 400

    spotify_url = get_spotify_link_for_song(media)
    orm_urls = UrlsForItem(spotify_url=spotify_url)
    orm_queue_item = QueueItem(user=to_user,queued_by_user=from_user,
                        urls=orm_urls,
                        listened=False,
                        date_queued=calendar.timegm(datetime.datetime.utcnow().utctimetuple()))

    db.session.add(orm_urls)

    if queue_item['type'] == 'song':
        artist = media['artist']
        orm_artist = Artist(name=artist['name'],
                            small_image_link=artist['images']['small'],
                            medium_image_link=artist['images']['medium'],
                            large_image_link=artist['images']['large'])

        album = media['album']
        orm_album = Album(name=album['name'])


        orm_song = SongItem(name=media['name'],
                            small_image_link=media['images']['small'],
                            medium_image_link=media['images']['medium'],
                            large_image_link=media['images']['large'])

        orm_song.artist = orm_artist
        orm_song.album = orm_album
        orm_queue_item.song_item = [orm_song]
        db.session.add(orm_queue_item)
        db.session.add(orm_song)
        db.session.add(orm_album)
        db.session.add(orm_artist)

    elif queue_item['type'] == 'artist':
        orm_artist = ArtistItem(name=media['name'],
                            small_image_link=media['images']['small'],
                            medium_image_link=media['images']['medium'],
                            large_image_link=media['images']['large'])

        orm_queue_item.artist_item = [orm_artist]
        db.session.add(orm_artist)

    elif queue_item['type'] == 'note':
        orm_note = NoteItem(text=media['text'])

        orm_queue_item.note_item = [orm_note]
        db.session.add(orm_note)

    db.session.commit()

    return jsonify({"status":"OK"})


def get_user(user_name):
    users = list(db.session.query(User).filter(User.uname == user_name))
    if not users:
        return None

    assert len(users) < 2
    return users[0]

def no_such_user(user_name):

    app.logger.warning("no such user %s" % user_name)
    return jsonify({"message":"no such user %s" % user_name}), 400

def is_friends(user1, user2):
    friends = list(db.session.query(Friend).filter(Friend.user_id == user1.id)\
                                 .filter(Friend.user_id == user2.id))
    if not friends:
        return False

    return True

def get_spotify_link_for_song(song):
    search_text = " ".join([song['name'], song['artist']['name'],
                           song['album']['name']])
    resp = requests.get("%s/search/1/track.json?q=%s" % (SP_API_URL, search_text))

    app.logger.warning(resp.status_code)
    if resp.status_code != 200 or not resp.json()['tracks']:
       return None

    link = resp.json()['tracks'][0]['href']
    return link

def get_spotify_link_for_artist(artist):
    search_text = artist['name']
    resp = requests.get("%s/search/1/artist.json?q=%s" % (SP_API_URL, search_text))
    link = resp.json()['artists'][0]['href']
    return link

def get_fb_friends(fb_id, access_token):
    resp = requests.get("%s/%s/friends?limit=5000&access_token=%s" %
                            (FB_API_URL, fb_id, access_token))
    if 'data' not in resp.json():
        return None

    friends = resp.json()['data']
    return friends
    






if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)


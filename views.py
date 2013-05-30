import datetime
import json
import calendar
import os
from functools import wraps

from flask import Flask, request, jsonify, session
from flask import redirect, request, current_app

from flask.ext.login import login_required, login_user, logout_user, current_user

import requests

from app import app, db, login_manager

from models import SongItem, User, Artist, Album, Friend, ArtistItem, NoteItem, UrlsForItem, QueueItem
from lastfm import LastFMer
from links import Linker

TS_API_KEY = app.config['TS_API_KEY']
TS_API_URL = app.config['TS_API_URL']
SP_API_URL = app.config['SP_API_URL']
LF_API_URL = app.config['LF_API_URL']
LF_API_KEY = app.config['LF_API_KEY']
FB_API_URL = app.config['FB_API_URL']

@login_manager.user_loader
def load_user(userid):
    return db.session.query(User).get(userid)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'OK'})

def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
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
    tracks = LastFMer.search_for_songs(search_text)
    artists = LastFMer.search_for_artists(search_text)
    results = {'trackResults':tracks, 'artistResults':artists}

    return jsonify(results)

@app.route('/user/<user_id>/listens', methods=['GET'])
@support_jsonp
def get_listens(user_id):
    user = get_user(user_id)
    
    if not user:
        return '', 404
    
    listens = []
    lastfm_name = user.lastfm_name

    if not lastfm_name:
        return '', 404
    

    lastfm_tracks = LastFMer.get_user_listens(lastfm_name)

    data = {'recentTracks':{ 'tracks':lastfm_tracks['tracks']}}

    data['recentTracks']['tracks'] = sorted(data['recentTracks']['tracks'], lambda k1, k2: k1['dateListened'] > k2['dateListened'])

    return jsonify(data)

@app.route('/', methods=['GET'])
@support_jsonp
def home():
    return jsonify({"hello":"there"})

@app.route('/user/<user_id>/friends', methods=['GET'])
@support_jsonp
@login_required
def get_friends(user_id):
    args = request.values
    access_token = args['accessToken']
    user = get_user(user_id)

    raise NotImplementedError

    return jsonify({})

@app.route('/user/<user_id>', methods=['PUT'])
@support_jsonp
@login_required
def change_user(user_id):
    args = request.json
    lastfm_name = args.get('lastFMUsername', None)
    device_token = args.get('deviceToken', None)

    user = get_user(user_id)

    if user != current_user:
        return '', 403

    if not user:
        return '', 404

    if lastfm_name:
        user.lastfm_name = lastfm_name

    if device_token:
        user.device_token = device_token

    db.session.add(user)
    db.session.commit()
    return jsonify(user.dictify())


@app.route('/login', methods=['POST'])
@support_jsonp
def login():
    args = request.json


    access_token = args['accessToken']
    fb_id = args['fbId']
    
    if not fb_user_is_valid(fb_id, access_token):
        return jsonify({'message': 'access_token invalid'}), 403
    
    user = get_user_by_fbid(fb_id)

    if not user:
        user = User(fb_id=fb_id, access_token=access_token,
                fullname=args['fullName'], image_link=args['imageLink'])

        db.session.add(user)
        db.session.commit()
    
    if login_user(user, remember=True):
        session.permanent = True
        return jsonify(user.dictify())
    
    return jsonify({'message': 'could not log in'}), 400

@app.route('/user/<user_id>/queue', methods=['GET'])
@support_jsonp
def get_queue(user_id):

    user = get_user(user_id)

    if not user:
        return no_such_user(user_id)

    items = db.session.query(QueueItem)\
        .filter(QueueItem.user_id == user.id).all()
    
    queue = []
    for item in items:
        queue.append(item.dictify())

    queue = sorted(queue, key=lambda x: (1*x['listened'], -1*x['dateQueued']))
    return jsonify({"queue":{"items":queue}})

@app.route('/user/<user_id>/queue/<item_id>', methods=['DELETE'])
@support_jsonp
@login_required
def delete_queue_item(user_id, item_id):
    user = get_user(user_id)

    if user != current_user:
        return '', 403

    queue_item = db.session.query(QueueItem)\
        .filter(QueueItem.user_id == user_id)\
        .filter(QueueItem.id == item_id)

    if not list(queue_item):
        return '', 404

    queue_item = queue_item.one()

    item_type, item = queue_item.get_item()
    db.session.delete(item)
    db.session.delete(queue_item)
    db.session.commit()

    return jsonify({'status': 'OK'})

@app.route('/user/<user_id>/queue/<item_id>', methods=['PUT'])
@support_jsonp
@login_required
def change_queue_item(user_id, item_id):
    listened = True if request.json['listened'] == 1 else False
    user = get_user(user_id)

    if user != current_user:
        return '', 403

    item = db.session.query(QueueItem)\
        .filter(QueueItem.user_id == user.id)\
        .filter(QueueItem.id == item_id).one()

    item.listened = listened
    db.session.add(item)
    db.session.commit()

    return jsonify({'status': 'OK'})

@app.route('/fbuser/<fb_id>/queue', methods=['POST'])
@support_jsonp
@login_required
def enqueue_item_by_fbid(fb_id):

    queue_item = request.json
    from_user_id = queue_item['fromUser']['userID']
    access_token = queue_item['fromUser']['accessToken']
    from_user = get_user(from_user_id)
    to_user = get_user_by_fbid(fb_id)
    if from_user != current_user:
        return '', 403

    if not from_user:
        return no_such_user(from_user)

    if not to_user:
        return no_such_user(to_user)

    return enqueue_item(to_user.id)

       
@app.route('/user/<user_id>/queue', methods=['POST'])
@support_jsonp
@login_required
def enqueue_item(user_id):

    queue_item = request.json
    from_user_id = queue_item['fromUser']['userID']
    access_token = queue_item['fromUser']['accessToken']
    media = queue_item[queue_item['type']]

    from_user = get_user(from_user_id)
    to_user = get_user(user_id)

    if from_user != current_user:
        return '', 403

    if not from_user:
        return no_such_user(from_user)

    if not to_user:
        return no_such_user(to_user)

    from_fb_id = from_user.fb_id
    to_fb_id = to_user.fb_id

    if not is_friends(from_fb_id, to_fb_id, access_token):
        return jsonify({'message':'users are not friends'}), 403
    
    orm_queue_item = QueueItem(user=to_user,queued_by_user=from_user,
                        urls=None,
                        listened=True if queue_item['listened'] == 'true' else False,
                        date_queued=calendar.timegm(datetime.datetime.utcnow().utctimetuple()))


    if queue_item['type'] == 'song':
        artist = media['artist']
        orm_artist = Artist(name=artist['name'],
                            small_image_link=artist['images']['small'],
                            medium_image_link=artist['images']['medium'],
                            large_image_link=artist['images']['large'],
                            extra_large_image_link=artist['images']['extraLarge'])

        album = media['album']
        orm_album = Album(name=album['name'])


        orm_song = SongItem(name=media['name'],
                            small_image_link=media['images']['small'],
                            medium_image_link=media['images']['medium'],
                            large_image_link=media['images']['large'],
                            extra_large_image_link=media['images']['extraLarge'])


        spotify_url = Linker.spotify_song(song=orm_song.name, artist=orm_artist.name)
        grooveshark_url = Linker.grooveshark(artist=orm_artist.name, song=orm_song.name)
        orm_urls = UrlsForItem(spotify_url=spotify_url, grooveshark_url=grooveshark_url)

        orm_song.artist = orm_artist
        orm_song.album = orm_album
        orm_queue_item.urls = orm_urls
        orm_queue_item.song_item = [orm_song]
        db.session.add_all([orm_queue_item, orm_song, orm_album, orm_artist, orm_urls])

    elif queue_item['type'] == 'artist':
        orm_artist = ArtistItem(name=media['name'],
                            small_image_link=media['images']['small'],
                            medium_image_link=media['images']['medium'],
                            large_image_link=media['images']['large'],
                            extra_large_image_link=media['images']['extraLarge'])


        spotify_url = Linker.spotify_artist(artist=orm_artist.name)
        grooveshark_url = Linker.grooveshark(artist=orm_artist.name)
        orm_urls = UrlsForItem(spotify_url=spotify_url, grooveshark_url=grooveshark_url)

        orm_queue_item.urls = orm_urls
        orm_queue_item.artist_item = [orm_artist]
        db.session.add_all([orm_artist, orm_queue_item, orm_urls])

    elif queue_item['type'] == 'note':
        orm_note = NoteItem(text=media['text'],
                            small_image_link=media['images']['small'],
                            medium_image_link=media['images']['medium'],
                            large_image_link=media['images']['large'],
                            extra_large_image_link=media['images']['extraLarge'])


        orm_urls = UrlsForItem(spotify_url="", grooveshark_url="")
        orm_queue_item.urls = orm_urls

        orm_queue_item.note_item = [orm_note]
        db.session.add_all([orm_note, orm_queue_item, orm_urls])

    db.session.commit()

    return jsonify(orm_queue_item.dictify())


def get_user(user_id):
    return db.session.query(User).get(user_id)

def fb_user_is_valid(fb_id, access_token):
    resp = requests.get("%s/me?access_token=%s" % (FB_API_URL, access_token))

    if resp.status_code != 200:
        return False

    if resp.json()['id'] != fb_id:
        return False
    
    return True

def get_user_by_fbid(fb_id):
    
    users = list(db.session.query(User).filter(User.fb_id == fb_id))

    if not users:
        return None

    return users[0]

def no_such_user(user_id):

    return jsonify({"message":"no such user %s" % user_id}), 404

def is_friends(user_id_1, user_id_2, access_token):
    if user_id_1 == user_id_2:
        return True
    resp = requests.get("%s/%s/friends/%s?access_token=%s" % (FB_API_URL, user_id_1, user_id_2, access_token))
    if resp.status_code != 200 or resp.json()['data'] == []:
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

def get_grooveshark_link(text):
    text_words = "+".join(text.split(" ")) 
    link = requests.get('%s/a/%s?format=json&key=%s' % (TS_API_URL, text_words, TS_API_KEY))

    if not link.json():
        return None
    
    return link.json()


def get_fb_friends(fb_id, access_token):
    resp = requests.get("%s/%s/friends?limit=5000&access_token=%s" %
                            (FB_API_URL, fb_id, access_token))
    if 'data' not in resp.json():
        return None

    friends = resp.json()['data']
    return friends
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)







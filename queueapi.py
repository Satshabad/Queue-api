import datetime
import json

from flask import Flask, request
from flask.ext.restful import Resource, Api

import requests

from queue import app, api, db

from models import Song, User, Artist, Album, Friend

LF_API_URL = app.config['LF_API_URL']
LF_API_KEY = app.config['LF_API_KEY']
FB_API_URL = app.config['FB_API_URL']

def fix_lastfm_data(data):
    data['recenttracks'][u'metadata'] = data['recenttracks'].pop('@attr')
    data['recenttracks'][u'tracks'] = data['recenttracks'].pop('track')

    for i, track in enumerate(data['recenttracks']['tracks']):

        track['album'][u'name'] = track['album'].pop('#text')
        track['streamable'] = int(track['streamable'])
        track['loved'] = int(track['loved'])

        del track['artist']['url']

        if track.has_key("date"):
            del track['date']['#text']
            track.update(track["date"])
            del track['date']

        if track.has_key("@attr"):
            track['nowplaying'] = True
            del track["@attr"]

        track[u'images'] = {}

        for image in track['image']:
            track['images'][image['size']] = image.pop('#text')

        del track['image']


        track['artist'][u'images'] = {}

        for image in track['artist']['image']:
             track['artist'][u'images'][image['size']] = image.pop('#text')

        del track['artist'][u'image']

    return data






class Listens(Resource):
    def get(self, user_name):
        data = requests.get("%smethod=user.getrecenttracks&user=%s&api_key=%sformat=json&extended=1" % (LF_API_URL, user_name, LF_API_KEY)).json()
        return fix_lastfm_data(data)


class Friends(Resource):
    def get(self, user_name):
        args = request.values
        access_token = args['access_token']
        user = get_user(user_name)

        if not user:
            return no_such_user(user_name)

        friends = []
        for friend in db.session.query(Friend).filter(Friend.user_id == user.id):
            friends.append(friend.dictify())

        return friends

class UserAPI(Resource):
    def post(self, user_name):
        args = request.json
        access_token = args['access_token']
        default = args['default']
        fb_id = args['fb_id']
        resp = requests.get("%s/%s/friends?limit=5000&access_token=%s" %
                                (FB_API_URL, fb_id, access_token))
        if 'data' not in resp.json():
            return {"status":500, "message": 'problem getting friends'}

        friends = resp.json()['data']
        user = User(user_name, access_token)
        for friend in friends:
            f = Friend(friend['name'], friend['id'], user)
            db.session.add(f)

        db.session.add(user)
        db.session.commit()

        return {"status":"OK"}


class Queue(Resource):
    def get(self, user_name):

        user = get_user(user_name)

        if not user:
            return no_such_user(user_name)
        orm_songs = db.session.query(Song).filter(Song.user_id == user.id).all()

        songs = []
        for orm_song in orm_songs:
            songs.append(orm_song.dictify())

        return {"queue":songs}

    def post(self, user_name):

        args = request.json
        access_token = args['access_token']
        song = args['song']
        from_user_name = args['from_user_name']

        from_user = get_user(from_user_name)
        to_users = get_user(to_user_name)

        if not from_user:
            return no_such_user(from_user)

        if not to_user:
            return no_such_user(to_user)

        if not is_friends(from_user, to_user):
           return {'status':400, 'message':'users are not friends'}

        artist = song['artist']
        orm_artist = Artist(name=artist['name'], mbid=artist['mbid'],
                            small_image_link=artist['images']['small'],
                            medium_image_link=artist['images']['medium'],
                            large_image_link=artist['images']['large'])

        album = song['album']
        orm_album = Album(name=album['name'], mbid=album['mbid'])

        orm_song = Song(user=to_user,queued_by_user=from_user,
                        listened=False, name=song['name'],
                        date_queued=datetime.datetime.utcnow(),
                        small_image_link=song['images']['small'],
                            medium_image_link=song['images']['medium'],
                            large_image_link=song['images']['large'])

        orm_song.artist = orm_artist
        orm_song.album = orm_album
        db.session.add(orm_song)
        db.session.add(orm_album)
        db.session.add(orm_artist)

        db.session.commit()

        return {"status":"OK"}


def get_user(user_name):
    users = list(db.session.query(User).filter(User.uname == user_name))
    if not users:
        return None

    assert len(users) < 2
    return users[0]

def no_such_user(user_name):
    return {"status":400, "message":"no such user %s" % user_name}

def isFriends(user1, user2):
    friends = list(db.session.query(Friend).filter(Friend.user_id == user1.id)\
                                 .filter(Friend.user_id == user2.id))
    if not friends:
        return False

    return True



api.add_resource(Listens, '/<string:user_name>/listens')
api.add_resource(Friends, '/<string:user_name>/friends')
api.add_resource(UserAPI, '/<string:user_name>')
api.add_resource(Queue, '/<string:user_name>/queue')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)


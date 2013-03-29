import datetime
import json

from flask import Flask, request
from flask.ext.restful import Resource, Api

import requests

from queue import app, api, db

from models import Song, User, Artist, Album

API_URL = app.config['API_URL']
API_KEY = app.config['API_KEY']

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
        data = requests.get("%smethod=user.getrecenttracks&user=%s&api_key=%sformat=json&extended=1" % (API_URL, user_name, API_KEY)).json()
        return fix_lastfm_data(data)


class Friends(Resource):
    def get(self, user_name):
        args = request.json
        auth = map(args.get, ['auth'])
        pass

class UserAPI(Resource):
    def post(self, user_name):
        args = request.json
        auth, default = map(args.get, ['auth', 'default'])
        resp = requests.get("http://graph.facebook.com/%s/friends?limit=5000" % auth)
        friends = resp.json()['data']
        user = User(user_name, auth)
        for friend in friends:
            f = Friend(friend['name'], friend['id'], user)
        db.session.add(u)
        db.session.commit()

        return {"status":"OK"}


class Queue(Resource):
    def get(self, user_name):
        user_id = db.session.query(User).filter(User.uname == user_name).one().id
        orm_songs = db.session.query(Song).filter(Song.user_id == user_id).all()

        songs = []
        for orm_song in orm_songs:
            songs.append(orm_song.dictify())

        return {"queue":songs}

    def post(self, user_name):

        args = request.json
        auth, song, from_user_name = map(args.get, ['auth', 'song', 'from_user_name'])
        from_user = db.session.query(User).filter(User.uname == from_user_name).one()
        to_user = db.session.query(User).filter(User.uname == user_name).one()

        if from_user and to_user:

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
        return {"status":"Not OK"}





api.add_resource(Listens, '/<string:user_name>/listens')
api.add_resource(Friends, '/<string:user_name>/friends')
api.add_resource(UserAPI, '/<string:user_name>')
api.add_resource(Queue, '/<string:user_name>/queue')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)


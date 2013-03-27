from flask import Flask, request
from flask.ext.restful import Resource, Api, reqparse

import requests

API_URL = "http://ws.audioscrobbler.com/2.0/?"
API_KEY = "7caf7bfb662c58f659df4446c7200f3c&"

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('song', type=dict)
parser.add_argument('auth', type=str)
parser.add_argument('to_user_id', type=str)

def fix_lastfm_data(data):
    data['recenttracks'][u'metadata'] = data['recenttracks'].pop('@attr')
    data['recenttracks'][u'tracks'] = data['recenttracks'].pop('track')

    for i, track in enumerate(data['recenttracks']['tracks']):

        track['album'][u'name'] = track['album'].pop('#text')


        del track['artist']['url']

        del track['date']['#text']

        track[u'images'] = track.pop('image')

        for image in track['images']:
            image[u'url'] = image.pop('#text')

        track['artist'][u'images'] = track['artist'].pop('image')

        for image in track['artist']['images']:
            image[u'url'] = image.pop('#text')

    return data








def get_args(args):
    pass

class Listens(Resource):
    def get(self, user_id):
        data = requests.get("%smethod=user.getrecenttracks&user=%s&api_key=%sformat=json&extended=1" % (API_URL, user_id, API_KEY)).json()
        return fix_lastfm_data(data)


class Friends(Resource):
    def get(self, user_id):
        args = parser.parse_args()
        auth = map(args.get, ['auth'])
        pass

class User(Resource):
    def post(self, user_id):
        args = parser.parse_args()
        auth, default = map(args.get, ['auth', 'default'])


class Queue(Resource):
    def get(self, user_id):
        pass

    def post(self, from_user_id):
        args = parser.parse_args()
        auth, song, to_user_id= map(args.get, ['auth', 'song', 'to_user_id'])

api.add_resource(Listens, '/<string:user_id>/listens')
api.add_resource(Friends, '/<string:user_id>/friends')
api.add_resource(User, '/<string:user_id>')
api.add_resource(Queue, '/<string:user_id>/queue')

if __name__ == '__main__':
    app.run()


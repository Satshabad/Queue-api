import datetime
import calendar

import requests

LF_API_URL = "http://ws.audioscrobbler.com/2.0/?"
LF_API_KEY = "7caf7bfb662c58f659df4446c7200f3c&"

class LastFMer():
    
    @staticmethod
    def get_user_listens(lastfm_name):
        data = requests.get("%smethod=user.getrecenttracks&user=%s&api_key=%sformat=json&extended=1"
                        % (LF_API_URL, lastfm_name, LF_API_KEY)).json()

        return LastFMer.format_data(data)

    @staticmethod
    def format_data(data):
        new_data = {}

        new_data['tracks'] = []
        for track in data['recenttracks']['track']:
            new_track = {}

            if track.has_key("date"):
                new_track['dateListened'] = track["date"]['uts']
            else:
                new_track['dateListened'] = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
   
            new_track['type'] = 'lastFM'


            new_track['song'] = {}
            new_track['song']['name'] = track['name']
            new_track['song']['images'] = LastFMer.parse_images(track)

            new_track['song']['album'] = track['album']
            new_track['song']['album'][u'name'] = track['album']['#text']

            new_track['song']['artist'] = {}
            new_track['song']['artist'] = track['artist']
            new_track['song']['artist']['images'] = LastFMer.parse_images(track['artist'])

            new_data['tracks'].append(new_track)

        return new_data

    @staticmethod
    def parse_images(data):
        new_images = {}
        if 'image' in data:
            for image in data['image']:
                if image['size'] == 'extralarge':
                    new_images['extraLarge'] = image['#text']
                else: 
                    new_images[image['size']] = image['#text']

        return new_images

import datetime
import calendar
from pprint import pprint

import requests

LF_API_URL = "http://ws.audioscrobbler.com/2.0/?"
LF_API_KEY = "7caf7bfb662c58f659df4446c7200f3c&"

class LastFMer():

    
    @staticmethod
    def complete_song(name, artist):
        data = requests.get("%smethod=track.getInfo&track=%s&artist=%s&autocorrect=1&api_key=%sformat=json&extended=0" % (LF_API_URL, name, artist, LF_API_KEY)).json()

        return LastFMer.parse_track(data['track'])
    
    @staticmethod
    def get_user_listens(lastfm_name):
        data = requests.get("%smethod=user.getrecenttracks&user=%s&api_key=%sformat=json&extended=1"
                        % (LF_API_URL, lastfm_name, LF_API_KEY)).json()

        return LastFMer.format_listen_data(data)

    @staticmethod
    def format_listen_data(data):
        new_data = []

        for track in data['recenttracks']['track']:
            new_data.append(LastFMer.parse_track(track))

        return new_data

    @staticmethod
    def parse_track(track):
        new_track = {}

        if track.has_key("date"):
            new_track['dateListened'] = track["date"]['uts']
        else:
            new_track['dateListened'] = calendar.timegm(datetime.datetime.utcnow().utctimetuple())

        new_track['type'] = 'lastFM'


        new_track['song'] = {}
        new_track['song']['name'] = track['name']
        if track.has_key('image'):
            new_track['song']['images'] = LastFMer.parse_images(track)
        elif track.has_key('album'):
            new_track['song']['images'] = LastFMer.parse_images(track['album'])
        elif track.has_key('artist'):
            new_track['song']['images'] = LastFMer.parse_images(track['artist'])
        else:
            new_track['song']['images'] = {}


        new_track['song']['album'] = track.get('album', {})
        if track.has_key('album'):
            if track['album'].has_key('#text'):
                new_track['song']['album'][u'name'] = track['album']['#text']
            elif track['album'].has_key('title'):
                new_track['song']['album'][u'name'] = track['album']['title']

        new_track['song']['artist'] = {}
        new_track['song']['artist'] = track['artist']
        new_track['song']['artist']['images'] = LastFMer.parse_images(track['artist'])

        return new_track



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


    @staticmethod
    def search_for_songs(search_text):
        search_url = "%smethod=track.search&track=%s&api_key=%sformat=json"
        track_results = requests.get(search_url %
                    (LF_API_URL, search_text, LF_API_KEY)).json()

        return LastFMer.format_song_search_data(track_results)

    @staticmethod
    def format_song_search_data(data):
        tracks = []

        if type(data) == type(u''):
            return tracks
 
        if type(data['results']['trackmatches']) == type(u''):
            return tracks
         

        if type(data['results']['trackmatches']['track']) == type([]):
            old_tracks = data['results']['trackmatches']['track']
        else:
            old_tracks = [ data['results']['trackmatches']['track'] ]

        for track in old_tracks:
            new_track = {}

            new_track['song'] = {}
            new_track['song']['images'] = LastFMer.parse_images(track)
            new_track['song']['album'] = {}
            new_track['song']['name'] = track['name']
            new_track['song']['artist'] = {'name':track['artist'], 'images':{}}
            new_track['listeners'] = track['listeners']

            tracks.append(new_track)

        return tracks

    @staticmethod
    def search_for_artists(search_text):
        search_url = "%smethod=artist.search&artist=%s&api_key=%sformat=json"
        artist_results = requests.get(search_url %
                    (LF_API_URL, search_text, LF_API_KEY)).json()
        return LastFMer.format_artist_search_data(artist_results)



    @staticmethod
    def format_artist_search_data(data):
        artists = []

        if type(data['results']['artistmatches']) == type(u''):
            return artists

        if type(data['results']['artistmatches']['artist']) == type({}):
            artist = data['results']['artistmatches']['artist']
            new_artist = {}

            new_artist['listeners'] = artist.get('listeners', 0)
            new_artist['artist'] = {}
            new_artist['artist']['name'] = artist['name']
            new_artist['artist']['images'] = LastFMer.parse_images(artist)

            return [new_artist]


        for artist in data['results']['artistmatches']['artist']:
            new_artist = {}

            new_artist['listeners'] = artist.get('listeners', 0)
            new_artist['artist'] = {}
            new_artist['artist']['name'] = artist['name']
            new_artist['artist']['images'] = LastFMer.parse_images(artist)

            artists.append(new_artist)

        return artists


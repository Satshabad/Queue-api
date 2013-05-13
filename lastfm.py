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

        return LastFMer.format_listen_data(data)

    @staticmethod
    def format_listen_data(data):
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


    @staticmethod
    def search_for_songs(search_text):
        search_url = "%smethod=track.search&track=%s&api_key=%sformat=json"
        track_results = requests.get(search_url %
                    (LF_API_URL, search_text, LF_API_KEY)).json()

        return LastFMer.format_song_search_data(track_results)

    @staticmethod
    def format_song_search_data(data):
        tracks = []

        if type(data['results']['trackmatches']) == type(u''):
            return tracks

        for track in data['results']['trackmatches']['track']:
            new_track = {}

            new_track['images'] = LastFMer.parse_images(track)
            new_track['name'] = track['name']
            new_track['images'] = track.get('images', {})
            new_track['artist'] = {'name':track['artist']}

            tracks.append(new_track)

        return tracks

    @staticmethod
    def search_for_artists(search_text):
        search_url = "%smethod=track.search&track=%s&api_key=%sformat=json"
        artist_results = requests.get(search_url %
                    (LF_API_URL, search_text, LF_API_KEY)).json()
        return LastFMer.format_artist_search_data(artist_results)



    @staticmethod
    def format_artist_search_data(data):
        artists = []

        if type(data['results']['artistmatches']) == type(u''):
            return artists

        for artist in data['results']['artistmatches']['artist']:
            new_artist = {}

            new_artist['images'] = LastFMer.parse_images(artist)
            new_artist['listeners'] = artist['listeners']
            new_artist['name'] = artist['name']

            artists.append(new_artist)

        return artists



def fix_lf_artist_search(data):
    fix_search_metadata(data)

    if type(data['artistmatches']) == type(u''):
        return {'artistResults':[]}

    data['artistResults'] = data.pop('artistmatches')['artist']
    if type(data['artistResults']) == type({}):
        data['artistResults'] = [data['artistResults']]

    del data['@attr']
    for artist in data['artistResults']:
        fix_image_data(artist)
        del artist['streamable']
        del artist['mbid']
        #del artist['listeners']
        del artist['url']

    return data


 

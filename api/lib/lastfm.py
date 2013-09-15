import datetime
import calendar
from pprint import pprint

import requests

LF_API_URL = "http://ws.audioscrobbler.com/2.0/?"
LF_API_KEY = "7caf7bfb662c58f659df4446c7200f3c&"


def complete_song(name, artist):
    data = requests.get(
        "%smethod=track.getInfo&track=%s&artist=%s&autocorrect=1&api_key=%sformat=json&extended=0" %
        (LF_API_URL, name, artist, LF_API_KEY)).json()

    try:
        track = data['track']
    except KeyError:
        return None

    return parse_track(track)


def get_user_listens(lastfm_name):
    data = requests.get("%smethod=user.getrecenttracks&user=%s&api_key=%sformat=json&extended=1"
                        % (LF_API_URL, lastfm_name, LF_API_KEY)).json()

    return format_listen_data(data)


def format_listen_data(data):
    new_data = []

    for track in data['recenttracks']['track']:
        new_data.append(parse_track(track))

    return new_data


def parse_track(track):
    new_track = {}

    new_track['dateListened'] = calendar.timegm(
        datetime.datetime.utcnow().utctimetuple())

    new_track['type'] = 'lastFM'

    new_track['song'] = {}
    new_track['song']['name'] = track.get('name', None)
    if 'image' in track:
        new_track['song']['images'] = parse_images(track)
    elif 'album' in track:
        new_track['song']['images'] = parse_images(track['album'])
    elif 'artist' in track:
        new_track['song']['images'] = parse_images(track['artist'])
    else:
        new_track['song']['images'] = {}

    new_track['song']['album'] = track.get('album', {})
    if 'album' in track:
        if '#text' in track['album']:
            new_track['song']['album'][u'name'] = track['album']['#text']
        elif 'title' in track['album']:
            new_track['song']['album'][u'name'] = track['album']['title']
        else:
            new_track['song']['album'][u'name'] = None

    new_track['song']['artist'] = track.get('artist', {})
    new_track['song']['artist']['images'] = parse_images(track['artist'])

    return new_track


def parse_images(data):
    new_images = {}
    if 'image' in data:
        for image in data['image']:
            if image['size'] == 'extralarge':
                new_images['extraLarge'] = image['#text']
            else:
                new_images[image['size']] = image['#text']

    return new_images


def search_for_songs(search_text):
    search_url = "%smethod=track.search&track=%s&api_key=%sformat=json"
    track_results = requests.get(search_url %
                                (LF_API_URL, search_text, LF_API_KEY)).json()

    return format_song_search_data(track_results)


def format_song_search_data(data):
    tracks = []

    if (isinstance(data, type(u'')) or
        'results' not in data or
        'trackmatches' not in data['results'] or
        isinstance(data['results']['trackmatches'], type(u'')) or
        'track' not in data['results']['trackmatches']):
        return tracks

    if isinstance(data['results']['trackmatches']['track'], type([])):
        old_tracks = data['results']['trackmatches']['track']
    else:
        old_tracks = [data['results']['trackmatches']['track']]

    for track in old_tracks:
        new_track = {}

        new_track['song'] = {}
        new_track['song']['images'] = parse_images(track)
        new_track['song']['album'] = {}
        new_track['song']['name'] = track.get('name', None)
        new_track['song']['artist'] = {
            'name': track.get('artist', None), 'images': {}}
        new_track['listeners'] = track.get('listeners', None)

        tracks.append(new_track)

    return tracks


def search_for_artists(search_text):
    search_url = "%smethod=artist.search&artist=%s&api_key=%sformat=json"
    artist_results = requests.get(search_url %
                                 (LF_API_URL, search_text, LF_API_KEY)).json()
    return format_artist_search_data(artist_results)


def format_artist_search_data(data):
    artists = []

    if (isinstance(data, type(u'')) or
        'results' not in data or
        'artistmatches' not in data['results'] or
        isinstance(data['results']['artistmatches'], type(u'')) or
        'artist' not in data['results']['artistmatches']):
        return artists

    if isinstance(data['results']['artistmatches']['artist'], type({})):
        artist = data['results']['artistmatches']['artist']
        new_artist = {}

        new_artist['listeners'] = artist.get('listeners', 0)
        new_artist['artist'] = {}
        new_artist['artist']['name'] = artist.get('name', None)
        new_artist['artist']['images'] = parse_images(artist)

        return [new_artist]

    for artist in data['results']['artistmatches']['artist']:
        new_artist = {}

        new_artist['listeners'] = artist.get('listeners', 0)
        new_artist['artist'] = {}
        new_artist['artist']['name'] = artist.get('name')
        new_artist['artist']['images'] = parse_images(artist)

        artists.append(new_artist)

    return artists

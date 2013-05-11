import calendar
import datetime
def fix_lastfm_listens_data(data):
    data['recentTracks'] = data.pop('recenttracks')
    data['recentTracks'][u'metadata'] = data['recentTracks'].pop('@attr')
    data['recentTracks'][u'tracks'] = data['recentTracks'].pop('track')

    for i, track in enumerate(data['recentTracks']['tracks']):
        del track['streamable']
        del track['loved']

        del track['artist']['url']
        del track['url']
        del track['mbid']
        del track['artist']['mbid']
        del track['album']['mbid']

        if track.has_key("date"):
            del track['date']['#text']
            track['dateListened'] = track["date"]['uts']
            del track['date']
        else:
            track['dateListened'] = calendar.timegm(datetime.datetime.utcnow().utctimetuple())

        if track.has_key("@attr"):
            del track["@attr"]

        fix_image_data(track)
        fix_image_data(track['artist'])

        track['song'] = {}
        track['song']['name'] = track.pop('name')
        track['song']['images'] = track.pop('images')
        track['song']['images']['extraLarge'] = track['song']['images'].pop('extralarge')
        track['song']['album'] = track.pop('album')
        track['song']['album'][u'name'] = track['song']['album'].pop('#text')
        track['song']['artist'] = track.pop('artist')
        track['song']['artist']['images']['extraLarge'] = track['song']['artist']['images'].pop('extralarge')




    return data

def fix_image_data(data):
    if 'image' in data:
        data['images'] = {}
        for image in data['image']:
            data['images'][image['size']] = image.pop('#text')

        del data['image']


def fix_lf_track_search(data):
    fix_search_metadata(data)
    data['trackResults'] = data.pop('trackmatches')['track']
    del data['@attr']

    for track in data['trackResults']:
        fix_image_data(track)
        del track['streamable']
        #del track['listeners']
        del track['mbid']
        del track['url']

    return data


def fix_lf_artist_search(data):
    fix_search_metadata(data)
    data['artistResults'] = data.pop('artistmatches')['artist']
    del data['@attr']

    for artist in data['artistResults']:
        fix_image_data(artist)
        del artist['streamable']
        del artist['mbid']
        #del artist['listeners']
        del artist['url']

    return data

def fix_search_metadata(data):
    data['metadata'] = {}
    data['metadata']['opensearch:Query'] = data.pop('opensearch:Query')
    data['metadata']['opensearch:totalResults'] = data.pop('opensearch:totalResults')
    data['metadata']['opensearch:startIndex'] = data.pop('opensearch:startIndex')
    data['metadata']['opensearch:itemsPerPage'] = data.pop('opensearch:itemsPerPage')

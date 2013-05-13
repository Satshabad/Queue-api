import calendar
import datetime
def fix_image_data(data):
    if 'image' in data:
        data['images'] = {}
        for image in data['image']:
            data['images'][image['size']] = image.pop('#text')

        del data['image']


def fix_lf_track_search(data):
    fix_search_metadata(data)

    if type(data['trackmatches']) == type(u''):
        return {'trackResults':[]}

    data['trackResults'] = data.pop('trackmatches')['track']
    del data['@attr']

    for track in data['trackResults']:
        fix_image_data(track)

        del track['streamable']
        del track['listeners']
        del track['mbid']
        del track['url']


        track['song'] = {}
        track['song']['name'] = track.pop('name')
        track['song']['images'] = track.pop('images', {})
        track['song']['images']['extraLarge'] = track['song']['images'].pop('extralarge', "")
        track['song']['artist'] = {'name':track.pop('artist')}

        track['type'] = 'lastFM'

    return data


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

def fix_search_metadata(data):
    data['metadata'] = {}
    data['metadata']['opensearch:Query'] = data.pop('opensearch:Query')
    data['metadata']['opensearch:totalResults'] = data.pop('opensearch:totalResults')
    data['metadata']['opensearch:startIndex'] = data.pop('opensearch:startIndex')
    data['metadata']['opensearch:itemsPerPage'] = data.pop('opensearch:itemsPerPage')

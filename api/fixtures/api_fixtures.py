import vcr
import inspect
too_soon_too_tell = {'name': "Too Soon To Tell",
                     'images': {'small': "http://image.com/image.jpeg",
                                'medium': 'http://image.com/image.jpeg',
                                'large': 'http://image.com/image.jpeg',
                                'extraLarge': ''},
                     'artist': {'name': "Todd Snider",
                                'images': {'small': "http://image.com/image.jpeg",
                                           'medium':
                                           'http://image.com/image.jpeg',
                                           'large':
                                           'http://image.com/image.jpeg',
                                           'extraLarge': 'http://image.com/image.jpeg'}},
                     'album': {'name': "Agnostic Hymns & Stoner Fables"}}


blah_note = {
    'text': 'blah',
    'images': {
        'small': 'http://image.com/image.jpeg',
        'medium': 'http://image.com/image.jpeg',
        'large': 'http://image.com/image.jpeg',
        'extraLarge': 'http://image.com/image.jpeg'}}

todd_snider = {
    'name': "Todd Snider",
    'images': {
        'small': "http://image.com/image.jpeg",
        'medium': 'http://image.com/image.jpeg',
        'large': 'http://image.com/image.jpeg',
        'extraLarge': 'http://image.com/image.jpeg'}}

def make_user(user_name):
    if user_name == "satshabad":
        return {'accessToken': "abc",
                'fbId': 456,
                'fullName': "satshabad",
                'imageLink': "http://image.com/jpeg",
                "deviceToken": "098876765",
                "badgeSetting": None,
                'lastFMUsername': 'satshabad',
                'twitterUsername': 'satshabad'}

    if user_name == "fateh":
        return {'accessToken': "def",
                'fbId': 789,
                'fullName': "fateh",
                'imageLink': "http://image.com/fateh.jpg",
                "deviceToken": "12jkh23hk",
                "badgeSetting": None,
                'lastFMUsername': 'fskhalsa',
                'twitterUsername': 'fs1034'}




def make_song_from(user, song=too_soon_too_tell, saved=False):
    return {'fromUser': user,
            'type': 'song',
            'saved': saved,
            'song': song}


def make_note_from(user, note=blah_note, saved=False):
    return {'fromUser': user,
            'type': 'note',
            'saved': saved,
            'note': note}


def make_artist_from(user, artist=todd_snider, saved=False):
    return {'fromuser': user,
            'type': 'artist',
            'saved': saved,
            'artist': artist}

vcr = vcr.VCR(
    cassette_library_dir='tests/cassettes'
)

def function_name():
    return inspect.stack()[1][3]

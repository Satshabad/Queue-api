from .models import SongItem, Artist, Album, UrlsForItem, NoteItem, ArtistItem
from api.lib import links, lastfm


def song_is_complete_enough(data):
    if data['artist']['images'] == {}:
        return False

    if data['album'] == {}:
        return False

    return True


def make_song_model(data):
    artist = data['artist']
    orm_artist = Artist(name=artist['name'],
                        small_image_link=artist['images'].get('small', None),
                        medium_image_link=artist['images'].get('medium', None),
                        large_image_link=artist['images'].get('large', None),
                        extra_large_image_link=artist['images'].get('extraLarge', None))

    album = data['album']
    orm_album = Album(name=album.get('name', None))

    orm_song = SongItem(name=data['name'],
                        small_image_link=data['images'].get('small', None),
                        medium_image_link=data['images'].get('medium', None),
                        large_image_link=data['images'].get('large', None),
                        extra_large_image_link=data['images'].get('extraLarge', None))

    orm_song.artist = orm_artist
    orm_song.album = orm_album

    return orm_song


def make_urls_for_song(data):
    name = data['name']
    artist = data['artist']['name']
    spotify_url = links.spotify_song(song=name, artist=artist)
    grooveshark_url = links.grooveshark(artist=artist, song=name)
    return (
        UrlsForItem(spotify_url=spotify_url, grooveshark_url=grooveshark_url)
    )


def create_song(data):
    if song_is_complete_enough(data):
        song = make_song_model(data)
    else:
        song = make_song_model(
            lastfm.complete_song(data['name'],
                                 data['artist']['name'])['song'])

    return song


def make_artist_model(data):
    orm_artist = ArtistItem(name=data['name'],
                            small_image_link=data['images'].get('small', None),
                            medium_image_link=data[
                                'images'].get('medium', None),
                            large_image_link=data['images'].get('large', None),
                            extra_large_image_link=data['images'].get('extraLarge', None))
    return orm_artist


def make_urls_for_artist(data):
    spotify_url = links.spotify_artist(artist=data['name'])
    grooveshark_url = links.grooveshark(artist=data['name'])
    return (
        UrlsForItem(spotify_url=spotify_url, grooveshark_url=grooveshark_url)
    )


def make_note_model(data):
    orm_note = NoteItem(text=data['text'],
                        small_image_link=data['images'].get('small', None),
                        medium_image_link=data['images'].get('medium', None),
                        large_image_link=data['images'].get('large', None),
                        extra_large_image_link=data['images'].get('extraLarge', None))

    return orm_note


def make_urls_for_note(data):
    return UrlsForItem(other_url=links.parse_from_text(data['text']))

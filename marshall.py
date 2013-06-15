from models import SongItem, Artist, Album, UrlsForItem
from links import Linker
from lastfm import LastFMer

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
    orm_album = Album(name=album['name'])


    orm_song = SongItem(name=data['name'],
                        small_image_link=data['images'].get('small', None),
                        medium_image_link=data['images'].get('medium', None),
                        large_image_link=data['images'].get('large', None),
                        extra_large_image_link=data['images'].get('extraLarge', None))

    orm_song.artist = orm_artist
    orm_song.album = orm_album

    return orm_song


def make_urls_for_song(name, artist):
    spotify_url = Linker.spotify_song(song=name, artist=artist)
    grooveshark_url = Linker.grooveshark(artist=artist, song=name)
    return UrlsForItem(spotify_url=spotify_url, grooveshark_url=grooveshark_url)

def create_song(data):
    if song_is_complete_enough(data):
        song = make_song_model(data)
    else:
        song = LastFMer.complete_song(data['name'], data['artist']['name'])
   

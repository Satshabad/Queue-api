import unittest
from pprint import pprint

from api.fixtures import vcr, function_name
from mock import patch
from expecter import expect

from api.models import marshall

class Marshall(unittest.TestCase):

    @patch('api.models.marshall.links.grooveshark') 
    @patch('api.models.marshall.links.spotify_song') 
    def it_makes_urls_for_song(self, spotify_song, grooveshark):
        data = {"artist": {"name":"Todd Snider", 
                           "images":{"small":"link", 
                           "medium":"link", 
                           "large":"link", 
                           "extraLarge":"link"}}, 
                "album":{"name":"Something"}, 
                "name":"Too Soon To Tell",
                "images":{"small":"link", 
                           "medium":"link", 
                           "large":"link", 
                           "extraLarge":"link"}}
        urls = marshall.make_urls_for_song(data)

    def it_knows_when_song_dont_have_artist_images(self):
        data = {"artist": {"name":"Todd Snider", "images":{}},
                "album":{"name":"Something"}, 
                "name":"Too Soon To Tell",
                "images":{"small":"link", 
                           "medium":"link", 
                           "large":"link", 
                           "extraLarge":"link"}}
    
        expect(marshall.song_is_complete_enough(data)) == False

    def it_knows_when_song_dont_have_album(self):
        data = {"artist": {"name":"Todd Snider", 
                           "images":{"small":"link", 
                           "medium":"link", 
                           "large":"link", 
                           "extraLarge":"link"}}, 
                "album":{}, 
                "name":"Too Soon To Tell",
                "images":{"small":"link", 
                           "medium":"link", 
                           "large":"link", 
                           "extraLarge":"link"}}

        expect(marshall.song_is_complete_enough(data)) == False

    def it_makes_a_song_model(self):
        data = {"artist": {"name":"Todd Snider", 
                           "images":{"small":"link", 
                           "medium":"link", 
                           "large":"link", 
                           "extraLarge":"link"}}, 
                "album":{"name":"Something"}, 
                "name":"Too Soon To Tell",
                "images":{"small":"link", 
                           "medium":"link", 
                           "large":"link", 
                           "extraLarge":"link"}}

        song = marshall.make_song_model(data)

        expect(song.name) == "Too Soon To Tell"
        expect(song.small_image_link) == "link"
        expect(song.artist.name) == "Todd Snider"
    
    def it_creates_song_when_not_enough_info(self):
        data = {"artist": {"name":"Todd Snider",
                            "images":{}},
                "name":"Too Soon To Tell",
                "images":{"small":"link", 
                           "medium":"link", 
                           "large":"link", 
                           "extraLarge":"link"}}

        with vcr.use_cassette(function_name() + '.yaml'):
            song = marshall.create_song(data)

        expect(song.name) == "Too Soon to Tell"
        expect(song.artist.name) == "Todd Snider"
 


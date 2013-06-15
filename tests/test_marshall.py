import unittest
from pprint import pprint

from mock import patch
from expecter import expect

from queue_app import marshall

class Marshall(unittest.TestCase):

    @patch('queue_app.marshall.Linker.grooveshark') 
    @patch('queue_app.marshall.Linker.spotify_song') 
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
    



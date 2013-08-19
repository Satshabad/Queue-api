import unittest
import json

import vcr
from mock import patch
from expecter import expect

from api import links

Linker = links.Linker

class LinkerSpec(unittest.TestCase):
    
    def it_finds_the_spotify_artist_link(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/spotify_artist.yaml'):
            link = Linker.spotify_artist(artist="corndawg")

        expect(link) == "spotify:artist:5xF2BAe0UcnCrOB40HmB0I"

    def it_doesnt_find_the_spotify_artist_link(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/not_spotify_artist.yaml'):
            link = Linker.spotify_artist(artist="corndawggggggggggg")

        expect(link) == None


    def it_finds_the_spotify_song_link(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/spotify_song.yaml'):
            link = Linker.spotify_song(song="chevy", artist="corndawg")

        expect(link) == "spotify:track:1jtSxb2CgTrX2RAa8aPnE6"

    def it_doesnt_find_the_spotify_song_link(self):
        with vcr.use_cassette('./fixtures/vcr_cassettes/not_spotify_artist.yaml'):
           link = Linker.spotify_song(song="chevyasdasdsa", artist="corndawg")

        expect(link) == None

    def it_finds_the_grooveshark_link(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/grooveshark_link.yaml'):
            link = Linker.grooveshark(song="Too Soon to Tell", artist="Todd Snider")

        expect(link) == "http://tinysong.com/Ypc9"

   
    def it_parses_out_the_url(self):
        text = "a string with a url http://google.com"
        expect(Linker.parse_from_text(text)) == "http://google.com"
          

    

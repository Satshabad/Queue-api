import unittest
import json

from mock import patch
from expecter import expect

from queue_app import links

Linker = links.Linker

class LinkerSpec(unittest.TestCase):
    
    @patch('queue_app.links.requests')
    def it_finds_the_spotify_artist_link(self, requests):
        requests.get.return_value.status_code = 200
        requests.get.return_value.json.return_value = json.loads("""{
                        "info": {
                            "num_results": 2,
                            "limit": 100,
                            "offset": 0,
                            "query": "corndawg",
                            "type": "artist",
                            "page": 1
                        },
                        "artists": [
                            {
                                "href": "spotify:artist:5xF2BAe0UcnCrOB40HmB0I",
                                "name": "Jonny Corndawg",
                                "popularity": "0.05587"
                            },
                            {
                                "href": "spotify:artist:0Eg9efneN98SMEif41qyAB",
                                "name": "Corndawg",
                                "popularity": "0.00016"
                            }
                        ]}""")

        link = Linker.spotify_artist(artist="corndawg")

        expect(link) == "spotify:artist:5xF2BAe0UcnCrOB40HmB0I"

    @patch('queue_app.links.requests')
    def it_doesnt_find_the_spotify_artist_link(self, requests):
        requests.get.return_value.json.return_value = json.loads("""{
                        "info": {
                            "num_results": 2,
                            "limit": 100,
                            "offset": 0,
                            "query": "corndawg",
                            "type": "artist",
                            "page": 1
                        },
                        "artists": [] }""")

        link = Linker.spotify_artist(artist="corndawg")

        expect(link) == None


    @patch('queue_app.links.requests')
    def it_finds_the_spotify_song_link(self, requests):
        requests.get.return_value.status_code = 200
        requests.get.return_value.json.return_value = json.loads(""" {
                        "info": {
                            "num_results": 2,
                            "limit": 100,
                            "offset": 0,
                            "query": "corndawg chevy",
                            "type": "track",
                            "page": 1
                        },
                        "tracks": [
                            {
                                "album": {
                                    "released": "2011",
                                    "href": "spotify:album:6KwB4z96EbNvNjTq1stCpZ",
                                    "name": "Down On The Bikini Line",
                                    "availability": {
                                        "territories": "CA US"
                                    }
                                },
                                "name": "Chevy Beretta",
                                "popularity": "0.29419",
                                "external-ids": [
                                    {
                                        "type": "isrc",
                                        "id": "US49S1100002"
                                    }
                                ],
                                "length": 185.785,
                                "href": "spotify:track:1jtSxb2CgTrX2RAa8aPnE6",
                                "artists": [
                                    {
                                        "href": "spotify:artist:5xF2BAe0UcnCrOB40HmB0I",
                                        "name": "Jonny Corndawg"
                                    }
                                ],
                                "track-number": "2"
                            }]
                    }""")

        link = Linker.spotify_song(song="chevy", artist="corndawg")

        expect(link) == "spotify:track:1jtSxb2CgTrX2RAa8aPnE6"

    @patch('queue_app.links.requests')
    def it_doesnt_find_the_spotify_song_link(self, requests):
        requests.get.return_value.json.return_value = json.loads(""" {
                        "info": {
                            "num_results": 2,
                            "limit": 100,
                            "offset": 0,
                            "query": "corndawg chevy",
                            "type": "track",
                            "page": 1
                        },
                        "tracks": []
                    }""")

        link = Linker.spotify_song(song="chevy", artist="corndawg")

        expect(link) == None

    @patch('queue_app.links.requests')
    def it_finds_the_grooveshark_link(self, requests):
        requests.get.return_value.status_code = 200
        requests.get.return_value.json.return_value = "http:\/\/tinysong.com\/Ypc9"

        link = Linker.grooveshark(song="Too Soon to Tell", artist="Todd Snider")

        expect(link) == "http:\/\/tinysong.com\/Ypc9"

        

    

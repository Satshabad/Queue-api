import unittest
import json

from expecter import expect
from mock import patch

from queue_app import lastfm

LastFMer = lastfm.LastFMer

class LastfmerSpec(unittest.TestCase):
    
    @patch('queue_app.lastfm.requests')
    def it_makes_get_request(self, requests):
        LastFMer.get_user_listens('satshabad')
        expect(requests.get.call_count) == 1

    def it_formats_the_recent_listens(self):
        formated_tracks = LastFMer.format_data(json.loads(""" {
                      "recenttracks":{
                        "track":[
                          {
                            "artist":{
                              "name":"Ursula 1000",
                              "mbid":"75f9a2a2-b76d-490d-8dd2-ab5c172bcd78",
                              "url":"Ursula 1000",
                              "image":[
                                {
                                  "#text":"http:\/\/userserve-ak.last.fm\/serve\/34\/82202.jpg",
                                  "size":"small"
                                },
                                {
                                  "#text":"http:\/\/userserve-ak.last.fm\/serve\/64\/82202.jpg",
                                  "size":"medium"
                                },
                                {
                                  "#text":"http:\/\/userserve-ak.last.fm\/serve\/126\/82202.jpg",
                                  "size":"large"
                                },
                                {
                                  "#text":"http:\/\/userserve-ak.last.fm\/serve\/252\/82202.jpg",
                                  "size":"extralarge"
                                }
                              ]
                            },
                            "loved":"0",
                            "name":"Mucho Tequila",
                            "streamable":"0",
                            "mbid":"f5084869-4b68-451d-be0c-cf14f6f52b39",
                            "album":{
                              "#text":"Kinda' Kinky",
                              "mbid":"f3d332ef-746f-4b0d-bfd9-8c8baeb7f48b"
                            },
                            "url":"http:\/\/www.last.fm\/music\/Ursula+1000\/_\/Mucho+Tequila",
                            "image":[
                              {
                                "#text":"http:\/\/userserve-ak.last.fm\/serve\/34s\/30083905.jpg",
                                "size":"small"
                              },
                              {
                                "#text":"http:\/\/userserve-ak.last.fm\/serve\/64s\/30083905.jpg",
                                "size":"medium"
                              },
                              {
                                "#text":"http:\/\/userserve-ak.last.fm\/serve\/126\/30083905.jpg",
                                "size":"large"
                              },
                              {
                                "#text":"http:\/\/userserve-ak.last.fm\/serve\/300x300\/30083905.jpg",
                                "size":"extralarge"
                              }
                            ],
                            "date":{
                              "#text":"13 May 2013, 00:12",
                              "uts":"1368403974"
                            }
                          }
                        ],
                        "@attr":{
                          "user":"fskhalsa",
                          "page":"1",
                          "perPage":"10",
                          "totalPages":"612",
                          "total":"6115"
                        }
                      }
                    }"""))

        expect(formated_tracks).contains('tracks')
        expect(formated_tracks['tracks'][0]).contains('type')
        expect(formated_tracks['tracks'][0]).contains('dateListened')

        expect(formated_tracks['tracks'][0]).contains('song')
        expect(formated_tracks['tracks'][0]['song']).contains('artist')
        expect(formated_tracks['tracks'][0]['song']['artist']).contains('images')
        expect(formated_tracks['tracks'][0]['song']['artist']).contains('name')

        expect(formated_tracks['tracks'][0]['song']).contains('album')
        expect(formated_tracks['tracks'][0]['song']['album']).contains('name')
        expect(formated_tracks['tracks'][0]['song']).contains('images')

                        
    def it_parses_and_formats_the_images(self):
        new_images = LastFMer.parse_images({'image':[{"#text":"link", "size":"small"}]})
        expect(new_images).contains('small')
        
    def it_renames_extralarge(self):
        new_images = LastFMer.parse_images({'image':[{"#text":"link", "size":"extralarge"}]})
        expect(new_images).contains('extraLarge')
        
        


import unittest
import json

from expecter import expect
from mock import patch
import vcr

from queue_app import lastfm

LastFMer = lastfm.LastFMer

class LastfmerSpec(unittest.TestCase):

    def it_completes_the_song(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/lastfm_completion.yaml'):
            track = LastFMer.complete_song("Too soon to tell", "Todd Snider")

        expect(track).contains('type')
        expect(track).contains('dateListened')

        expect(track).contains('song')

        expect(track['song']).contains('images')

        expect(track['song']).contains('artist')
        expect(track['song']['artist']).contains('images')
        expect(track['song']['artist']).contains('name')

        expect(track['song']).contains('album')
        expect(track['song']['album']).contains('name')

    def it_completes_the_song_as_best_it_can(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/lastfm_completion_no_album.yaml'):
            track = LastFMer.complete_song("Gimme Some Lovin' ", " Spirit")

        expect(track).contains('type')
        expect(track).contains('dateListened')

        expect(track).contains('song')
        expect(track['song']).contains('images')

        expect(track['song']).contains('artist')
        expect(track['song']['artist']).contains('images')
        expect(track['song']['artist']).contains('name')

        expect(track['song']).contains('album')



    def it_gets_the_users_listens(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/lastfm_listens.yaml'):
            listens = LastFMer.get_user_listens('satshabad')

        expect(listens).contains('tracks')
        expect(listens['tracks'][0]).contains('type')
        expect(listens['tracks'][0]).contains('dateListened')

        expect(listens['tracks'][0]).contains('song')

        expect(listens['tracks'][0]['song']).contains('images')

        expect(listens['tracks'][0]['song']).contains('artist')
        expect(listens['tracks'][0]['song']['artist']).contains('images')
        expect(listens['tracks'][0]['song']['artist']).contains('name')

        expect(listens['tracks'][0]['song']).contains('album')
        expect(listens['tracks'][0]['song']['album']).contains('name')

                        
    def it_parses_and_formats_the_images(self):
        new_images = LastFMer.parse_images({'image':[{"#text":"link", "size":"small"}]})
        expect(new_images).contains('small')
        
    def it_renames_extralarge(self):
        new_images = LastFMer.parse_images({'image':[{"#text":"link", "size":"extralarge"}]})
        expect(new_images).contains('extraLarge')
        
        
    # Search 

    def it_searches_for_artists(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/lastfm_artist_search.yaml'):
            result = LastFMer.search_for_artists("Love")

        expect(result[0]).contains('artist')
        expect(result[0]['artist']).contains('name')

        expect(result[0]['artist']).contains('images')
        expect(result[0]['artist']['images']).contains('small')
        expect(result[0]['artist']['images']).contains('medium')
        expect(result[0]['artist']['images']).contains('large')
        expect(result[0]['artist']['images']).contains('extraLarge')

 
        expect(result[0]).contains('listeners')

    def it_searches_for_artists_with_no_listeners(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/lastfm_artist_search_no_listens.yaml'):
            result = LastFMer.search_for_artists("firewater")

        expect(result[0]).contains('artist')
        expect(result[0]['artist']).contains('name')

        expect(result[0]['artist']).contains('images')
        expect(result[0]['artist']['images']).contains('small')
        expect(result[0]['artist']['images']).contains('medium')
        expect(result[0]['artist']['images']).contains('large')
        expect(result[0]['artist']['images']).contains('extraLarge')

 
        expect(result[0]).contains('listeners')



    def it_searches_for_artists(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/lastfm_artist_search_bad.yaml'):
            result = LastFMer.search_for_artists("askdjaskdjS")

        expect(result) == []


    def it_searches_for_songs(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/lastfm_song_search.yaml'):
            result = LastFMer.search_for_songs("Love")

        expect(result[0]).contains('song')
        expect(result[0]['song']).contains('name')

        expect(result[0]['song']).contains('images')
        expect(result[0]['song']['images']).contains('small')
        expect(result[0]['song']['images']).contains('medium')
        expect(result[0]['song']['images']).contains('large')
        expect(result[0]['song']['images']).contains('extraLarge')

 
        expect(result[0]['song']).contains('artist')
        expect(result[0]['song']['artist']).contains('name')
        expect(result[0]['song']['artist']).contains('images')

        expect(result[0]['song']).contains('album')

        expect(result[0]).contains('listeners')

    def it_searches_for_a_single_songs(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/lastfm_song_search_single.yaml'):
            result = LastFMer.search_for_songs("Wake up Motopony")

        expect(result[0]).contains('song')
        expect(result[0]['song']).contains('name')

        expect(result[0]['song']).contains('images')
        expect(result[0]['song']['images']).contains('small')
        expect(result[0]['song']['images']).contains('medium')
        expect(result[0]['song']['images']).contains('large')
        expect(result[0]['song']['images']).contains('extraLarge')

 
        expect(result[0]['song']).contains('artist')
        expect(result[0]['song']['artist']).contains('name')
        expect(result[0]['song']['artist']).contains('images')

        expect(result[0]['song']).contains('album')

        expect(result[0]).contains('listeners')

    def it_searches_for_songs_but_finds_none_for_single_letter(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/lastfm_song_search_bad_1.yaml'):
            result = LastFMer.search_for_songs("S")

        expect(result) == []

    def it_searches_for_songs_but_finds_none_for_nonsense(self):

        with vcr.use_cassette('./fixtures/vcr_cassettes/lastfm_song_search_bad_2.yaml'):
            result = LastFMer.search_for_songs("Sasdasdasdjlasdj")

        expect(result) == []
     
        

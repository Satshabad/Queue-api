import unittest
import json

import vcr
from expecter import expect
from mock import patch, MagicMock

from queue_app import twit

Twitterer = twit.Twitterer

class TwittererSpec(unittest.TestCase):


    @patch('queue_app.twit.LastFMer')
    @patch('queue_app.twit.twitter')
    def it_uses_lastfm_to_find_song(self, twitter, LastFMer):
        LastFMer.complete_song.return_value = {}
        tweet = MagicMock()
        tweet.text = "Wake up by Motopony, from #SoundHound http:\/\/t.co\/n2egIeV5dC"
        tweet.created_at = "Thu May 30 00:00:20 +0000 2013"
        twitter.Api.return_value.GetUserTimeline = lambda x: [tweet]
        
        tracks = Twitterer.get_user_listens('satshabad')

        expect(tracks).contains('tracks')
        expect(tracks['tracks'][0]).contains('type')
        expect(tracks['tracks'][0]).contains('dateListened')
        
    def it_parses_the_search_text(self):
        search_texts = Twitterer.parse_search_text_into_name_and_artist('Wake up by Motopony, on #SoundHound http://link.com')
        expect(search_texts) == ("Wake up ", " Motopony")
        



 

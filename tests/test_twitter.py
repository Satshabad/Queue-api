import unittest
import json

from expecter import expect
from mock import patch, MagicMock

from queue_app import twitter

Twitterer = twitter.Twitterer

class TwittererSpec(unittest.TestCase):

    def setUp(self):
        twitter.echonest = MagicMock
    

    @patch('queue_app.twitter.echonest')
    @patch('queue_app.twitter.requests')
    def it_uses_echonest_to_find_song(self, requests, echonest):
        requests.get.return_value.json.return_value = [{'text':'Wake up by Motopony, on #SoundHound', 
                                            'created_at':'Mon May 13 00:22:39 +0000 2013'} ]
    
        echonest.find_song.return_value = {}

        tracks = Twitterer.get_user_listens('satshabad')

        echonest.find_song.called_once_with("Wake up  Motopony")
        expect(requests.get.call_count) == 1
        expect(tracks).contains('tracks')
        expect(tracks['tracks'][0]).contains('type')
        expect(tracks['tracks'][0]).contains('dateListened')


    def it_pulls_out_the_soundhound_tweets(self):
        sh_tweets = Twitterer.extract_soundhound_tweets([{'text':'Wake up by Motopony, on #SoundHound'},
                                                        {'text':'A random tweet'}])
        expect(sh_tweets) ==[{'text':'Wake up by Motopony, on #SoundHound'}]
        
    def it_parses_the_search_text(self):
        search_texts = Twitterer.parse_search_text('Wake up by Motopony, on #SoundHound http://link.com')
        expect(search_texts) == "Wake up  Motopony"
        
    def it_extracts_to_tweet_date(self):
        utc_string = Twitterer.extract_utc_date({'created_at':'Mon May 13 00:22:39 +0000 2013' })
        expect(utc_string) == "1368404559"
        



 

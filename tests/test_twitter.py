import unittest
import json

from api.fixtures import vcr
from expecter import expect
from mock import patch, MagicMock

from api.lib import twit


class TwitSpec(unittest.TestCase):

    @patch('api.lib.lastfm.complete_song')
    @patch('api.lib.twit.twitter')
    def it_uses_lastfm_to_find_song(self, twitter, complete_song):
        complete_song.return_value = {}
        tweet = MagicMock()
        tweet.text = "Wake up by Motopony, from #SoundHound http:\/\/t.co\/n2egIeV5dC"
        tweet.created_at = "Thu May 30 00:00:20 +0000 2013"
        twitter.Api.return_value.GetUserTimeline = lambda x: [tweet]

        tracks = twit.get_user_listens('satshabad')

        expect(tracks[0]).contains('type')
        expect(tracks[0]).contains('dateListened')

    def it_parses_the_search_text(self):
        search_texts = twit.name_and_artist_from_text(
            'Wake up by Motopony, on #SoundHound http://link.com')
        expect(search_texts) == ("Wake up ", " Motopony")

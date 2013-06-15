import calendar
import datetime
import urllib2

import twitter

from lastfm import LastFMer

TW_CONSUMER_KEY = 'zSjlv6b1qqnagq9bBfMF0A'
TW_CONSUMER_SECRET = '78VqsXl464MCY8vG7oIKs0amVF8XK7SzyTF4pv8bI'
TW_ACCESS_TOKEN_KEY = "41949661-sXrAJfK6rXYBLJomW3IFhM1O1jObLhj7qNnWR3A"
TW_ACCESS_TOKEN_SECRET = "nMzyMyB93cEqyTGABQfJMLrPHyWeioseunfG6NRudVc"

class Twitterer():
   
    @staticmethod

    def get_user_listens(user_name):
        api = twitter.Api(consumer_key=TW_CONSUMER_KEY, consumer_secret=TW_CONSUMER_SECRET,  access_token_key=TW_ACCESS_TOKEN_KEY, access_token_secret=TW_ACCESS_TOKEN_SECRET)    
        tweets = api.GetUserTimeline(user_name)
        sh_tweets = Twitterer.extract_soundhound_tweets(tweets)
        tracks = []
        for tweet in sh_tweets:
            name, artist = Twitterer.parse_search_text_into_name_and_artist(tweet.text)
            song = LastFMer.complete_song(name, artist)
            song['dateListened'] = Twitterer.extract_utc_date(tweet)
            song['type'] = 'SoundHound'
            tracks.append(song)

        return tracks
            
    @staticmethod
    def extract_soundhound_tweets(tweets):
        return [ tweet for tweet in tweets if '#SoundHound' in tweet.text ]

    @staticmethod
    def extract_utc_date(tweet):
        return str(calendar.timegm(datetime.datetime.strptime(tweet.created_at, 
                                '%a %b %d %H:%M:%S +0000 %Y').utctimetuple()))

    @staticmethod
    def parse_search_text_into_name_and_artist(text):
        return tuple(text.split(',')[0].split('by')[:2])







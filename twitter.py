import calendar
import datetime

import requests

#import echonest
echonest = 2

TWITTER_URL ="https://api.twitter.com/1/statuses/user_timeline.json?" 

class Twitterer():
   
    @staticmethod
    def get_user_listens(user_name):
    
        tweets = requests.get('%sscreen_name=%s' % (TWITTER_URL, user_name)).json()
        sh_tweets = Twitterer.extract_soundhound_tweets(tweets)
        
        tracks = []
        for tweet in sh_tweets:
            song = echonest.find_song(Twitterer.parse_search_text(tweet['text']))
            song['dateListened'] = Twitterer.extract_utc_date(tweet)
            song['type'] = 'SoundHound'
            tracks.append(song)

        return {'tracks':tracks}
            
    @staticmethod
    def extract_soundhound_tweets(tweets):
        return [ tweet for tweet in tweets if '#SoundHound' in tweet['text']  ]

    @staticmethod
    def extract_utc_date(tweet):
        return str(calendar.timegm(datetime.datetime.strptime(tweet['created_at'], 
                                '%a %b %d %H:%M:%S +0000 %Y').utctimetuple()))

    @staticmethod
    def parse_search_text(text):
        return ''.join(text.split(',')[0].split('by'))







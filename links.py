import requests

SP_API_URL = "http://ws.spotify.com"

TS_API_KEY = "6b08a682cc42b6eda827a1d1a9ab838a"
TS_API_URL =  "http://tinysong.com"

class Linker():
    
    @staticmethod
    def spotify_artist(artist):
        
        resp = requests.get("%s/search/1/artist.json?q=%s" % (SP_API_URL, artist))

        if resp.status_code != 200:
            return ""

        data = resp.json()['artists']

        if data == []:
            return ""

        return data[0]['href']

    @staticmethod
    def spotify_song(song, artist):
        
        resp = requests.get("%s/search/1/track.json?q=%s" % (SP_API_URL, "+".join([artist, song])))

        if resp.status_code != 200:
            return ""

        data = resp.json()['tracks']

        if data == []:
            return ""

        return data[0]['href']

    @staticmethod
    def grooveshark(artist, song=""):
        link = requests.get('%s/a/%s?format=json&key=%s' % (TS_API_URL, " ".join([artist, song]), TS_API_KEY))

        if link.status_code != 200:
            return ""

        if not link.json():
            return ""
    
        return link.json()



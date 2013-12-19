import re
import requests

SP_API_URL = "http://ws.spotify.com"

TS_API_KEY = "6b08a682cc42b6eda827a1d1a9ab838a"
TS_API_URL =  "http://tinysong.com"

YT_API_URL = "http://gdata.youtube.com/feeds/api/"
YT_API_KEY = "AI39si7qa5aQEPMoNkM0d0gly0PDmR3hw6zGjMS_89TadypXqAPDeVIYXfhkLKteahLzDJcCQp3DKcOy8tRRPXLDmMje_i81_w"

def spotify_artist(artist):
    resp = requests.get("%s/search/1/artist.json?q=%s" % (SP_API_URL, artist))

    if resp.status_code != 200:
        return None

    data = resp.json()['artists']

    if data == []:
        return None

    return data[0]['href']

def spotify_song(song, artist):
    resp = requests.get("%s/search/1/track.json?q=%s" % (SP_API_URL, "+".join([artist, song])))

    if resp.status_code != 200:
        return None

    data = resp.json()['tracks']

    if data == []:
        return None

    return data[0]['href']

def grooveshark(artist, song=""):
    link = requests.get('%s/a/%s?format=json&key=%s' % (TS_API_URL, " ".join([artist, song]), TS_API_KEY))

    if link.status_code != 200:
        return None

    try:
        string_url = link.json()

        if not string_url
            return None

        return string_url

    except Exception:
        # TODO log this exception
        return None


def youtube(song, artist):
    query = song + " " + artist
    resp = requests.get("{}videos?max-results=1&alt=json&q={}".format(YT_API_URL, query),
                        headers={"x-gdata-key": "key={}".format(YT_API_KEY)})
    if not resp.json():
        return None

    link_types = resp.json()['feed']['entry'][0]["media$group"]["media$content"]

    for link_type in link_types:
        if link_type['type'] == u'application/x-shockwave-flash':
            return link_type['url']


def parse_from_text(text):
    match = re.search("(?P<url>https?://[^\s]+)", text)
    if match:
        return match.group("url")

    return None

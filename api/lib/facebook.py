import requests

FB_API_URL = "https://graph.facebook.com"


def verify(fb_id, access_token):
    resp = requests.get("%s/me?access_token=%s" % (FB_API_URL, access_token))

    if resp.status_code != 200:
        return False

    if resp.json()['id'] != fb_id:
        return False

    return True


def are_friends(fb_id_1, fb_id_2, access_token):
    url = "{}/{}/friends/{}?access_token={}"

    resp = requests.get(url.format(FB_API_URL,
                                   fb_id_1,
                                   fb_id_2,
                                   access_token))

    if resp.status_code != 200 or resp.json()['data'] == []:
        return False

    return True

import datetime
import json
import calendar
import os
from functools import wraps
from pprint import pprint
from logging import getLogger

from flask import Flask, request, jsonify, session
from flask import redirect, request, current_app

from flask.ext.login import login_required, login_user, logout_user, current_user

import requests

from app import app, db, login_manager

from models import SongItem, User, Artist, Album, Friend, ArtistItem, NoteItem, UrlsForItem, QueueItem
import lastfm
from links import Linker
import twit
import marshall

log = getLogger()

TS_API_KEY = app.config['TS_API_KEY']
TS_API_URL = app.config['TS_API_URL']
SP_API_URL = app.config['SP_API_URL']
LF_API_URL = app.config['LF_API_URL']
LF_API_KEY = app.config['LF_API_KEY']
FB_API_URL = app.config['FB_API_URL']

@login_manager.user_loader
def load_user(userid):
    return db.session.query(User).get(userid)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'OK'})

def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
            return current_app.response_class(content, mimetype='application/json')
        else:
            return f(*args, **kwargs)
    return decorated_function

@app.route('/search/<search_text>', methods=['GET'])
@support_jsonp
def search(search_text):
    tracks = lastfm.search_for_songs(search_text)[:5]
    artists = lastfm.search_for_artists(search_text)[:5]
    results = {'trackResults':tracks, 'artistResults':artists}

    return jsonify(results)

@app.route('/user/<user_id>/listens', methods=['GET'])
@support_jsonp
def get_listens(user_id):
    user = get_user(user_id)
    
    if not user:
        return '', 404
    
    listens = []
    if user.lastfm_name :
        listens.extend(lastfm.get_user_listens(user.lastfm_name))
    if user.twitter_name:
        listens.extend(twit.get_user_listens(user.twitter_name))
    
    data = {'recentTracks':{ 'tracks':sorted(listens, lambda k1, k2: k1['dateListened'] > k2['dateListened'])}}

    return jsonify(data)

@app.route('/', methods=['GET'])
@support_jsonp
def home():
    return jsonify({"hello":"there"})

@app.route('/user/<user_id>', methods=['PUT'])
@support_jsonp
@login_required
def change_user(user_id):
    args = request.json
    lastfm_name = args.get('lastFMUsername', None)
    twitter_name = args.get('twitterUsername', None)
    device_token = args.get('deviceToken', None)
    badge_setting = args.get('badgeSetting', None)

    user = get_user(user_id)

    if user != current_user:
        return '', 403

    if not user:
        return '', 404

    if lastfm_name != None:
        user.lastfm_name = lastfm_name

    if twitter_name != None:
        user.twitter_name = twitter_name

    if device_token != None:
        user.device_token = device_token

    if badge_setting != None:
        user.badge_setting = badge_setting
        recalc_badge_num(user.id)

    db.session.add(user)
    db.session.commit()
    return jsonify(user.dictify())


@app.route('/login', methods=['POST'])
@support_jsonp
def login():
    args = request.json
    log.debug(args)
    access_token = args['accessToken']
    fb_id = args['fbId']
    
    if not fb_user_is_valid(fb_id, access_token):
        return jsonify({'message': 'access_token invalid'}), 403
    
    user = get_user_by_fbid(fb_id)

    if not user:
        user = User(fb_id=fb_id, access_token=access_token,
                    fullname=args['fullName'], 
                    image_link=args['imageLink'], 
                    badge_setting=args.get('badgeSetting'),
                    device_token=args.get('deviceToken'),
                    badge_num=0)


        db.session.add(user)
        db.session.commit()
    
    if login_user(user, remember=True):
        session.permanent = True
        return jsonify(user.dictify())
    
    return jsonify({'message': 'could not log in'}), 400

@app.route('/user/<user_id>/queue', methods=['GET'])
@support_jsonp
def get_queue(user_id):

    user = get_user(user_id)

    if not user:
        return no_such_user(user_id)

    items = db.session.query(QueueItem)\
        .filter(QueueItem.user_id == user.id).all()
    
    queue = []
    for item in items:
        queue.append(item.dictify())

    return jsonify({'queue': {'items': list(reversed(queue))}} )


@app.route('/user/<user_id>/sent', methods=['GET'])
@support_jsonp
def get_sent(user_id):
    user = get_user(user_id)

    if not user:
        return no_such_user(user_id)

    items = db.session.query(QueueItem)\
        .filter(QueueItem.queued_by_id == user.id).all()

    queue = []
    for item in items:
        queue.append(item.dictify())

    return jsonify({'queue': {'items': list(reversed(queue))}} )

@app.route('/user/<user_id>/queue/<item_id>', methods=['DELETE'])
@support_jsonp
@login_required
def delete_queue_item(user_id, item_id):
    user = get_user(user_id)

    if user != current_user:
        return '', 403

    queue_item = db.session.query(QueueItem)\
        .filter(QueueItem.user_id == user_id)\
        .filter(QueueItem.id == item_id)

    if not list(queue_item):
        return '', 404

    queue_item = queue_item.one()

    was_shared = queue_item.queued_by_id != queue_item.user_id
    was_listened = queue_item.listened

    item_type, item = queue_item.get_item()
    db.session.delete(item)
    db.session.delete(queue_item)

    if user.badge_setting == "unlistened":
        if not was_listened:
            user.badge_num -= 1

            send_push_message(user.device_token, badge_num=user.badge_num)

    if user.badge_setting == "shared":
        if not was_listened and was_shared:
            user.badge_num -= 1

            send_push_message(user.device_token, badge_num=user.badge_num)

    db.session.add(user)
    db.session.commit()

    return jsonify({'status': 'OK'})

@app.route('/user/<user_id>/queue/<item_id>', methods=['PUT'])
@support_jsonp
@login_required
def change_queue_item(user_id, item_id):
    listened = True if request.json['saved'] == 1 else False
    user = get_user(user_id)

    if user != current_user:
        return '', 403

    item = db.session.query(QueueItem)\
        .filter(QueueItem.user_id == user.id)\
        .filter(QueueItem.id == item_id).one()

    was_listened = item.listened
    was_shared = item.queued_by_id != item.user_id
    item.listened = listened
    db.session.add(item)

    if user.badge_setting == "unlistened":
        if listened and not was_listened:
            user.badge_num -= 1
            send_push_message(user.device_token, badge_num=user.badge_num)

        if not listened and was_listened:
            user.badge_num += 1
            send_push_message(user.device_token, badge_num=user.badge_num)

    if user.badge_setting == "shared":
        if was_shared:
            if listened and not was_listened:
                user.badge_num -= 1
                send_push_message(user.device_token, badge_num=user.badge_num)

            if not listened and was_listened:
                user.badge_num += 1
                send_push_message(user.device_token, badge_num=user.badge_num)

    db.session.add(user)

    db.session.commit()

    return jsonify(item.dictify())

@app.route('/fbuser/<fb_id>/queue', methods=['POST'])
@support_jsonp
@login_required
def enqueue_item_by_fbid(fb_id):

    queue_item = request.json
    from_user_id = queue_item['fromUser']['userID']
    access_token = queue_item['fromUser']['accessToken']
    from_user = get_user(from_user_id)
    to_user = get_user_by_fbid(fb_id)
    if from_user != current_user:
        return '', 403

    if not from_user:
        return no_such_user(from_user)

    if not to_user:
        return no_such_user(to_user)

    return enqueue_item(to_user.id)

       
@app.route('/user/<user_id>/queue', methods=['POST'])
@support_jsonp
@login_required
def enqueue_item(user_id):

    queue_item = request.json
    from_user_id = queue_item['fromUser']['userID']
    access_token = queue_item['fromUser']['accessToken']
    media = queue_item[queue_item['type']]

    from_user = get_user(from_user_id)
    to_user = get_user(user_id)

    if from_user != current_user:
        return '', 403

    if not from_user:
        return no_such_user(from_user)

    if not to_user:
        return no_such_user(to_user)

    from_fb_id = from_user.fb_id
    to_fb_id = to_user.fb_id

    if not is_friends(from_fb_id, to_fb_id, access_token):
        return jsonify({'message':'users are not friends'}), 403
    
    orm_queue_item = QueueItem(user=to_user,queued_by_user=from_user,
                        urls=None,
                        listened=False,
                        date_queued=calendar.timegm(datetime.datetime.utcnow().utctimetuple()))


    if queue_item['type'] == 'song':
        orm_song = marshall.create_song(media)
        orm_urls = marshall.make_urls_for_song(media)

        orm_queue_item.urls = orm_urls
        orm_queue_item.song_item = [orm_song]
        db.session.add_all([orm_queue_item, orm_song, orm_urls])

    elif queue_item['type'] == 'artist':
        orm_artist = marshall.make_artist_model(media)
        orm_urls = marshall.make_urls_for_artist(media)

        orm_queue_item.urls = orm_urls
        orm_queue_item.artist_item = [orm_artist]
        db.session.add_all([orm_artist, orm_queue_item, orm_urls])

    elif queue_item['type'] == 'note':
        orm_note = marshall.make_note_model(media)
        orm_urls = marshall.make_urls_for_note(media)

        orm_queue_item.urls = orm_urls
        orm_queue_item.note_item = [orm_note]
        db.session.add_all([orm_note, orm_queue_item, orm_urls])


    if from_user.id != to_user.id and to_user.device_token:
        if to_user.badge_setting == "shared":
            to_user.badge_num += 1
            send_push_message(to_user.device_token,
                          message= "%s shared a %s with you" % (from_user.fullname, queue_item['type']), 
                          badge_num=to_user.badge_num, 
                          name=from_user.fullname, item_type=queue_item['type'])
        else:
            send_push_message(to_user.device_token,
                          message= "%s shared a %s with you" % (from_user.fullname, queue_item['type']), 
                          name=from_user.fullname, item_type=queue_item['type'])

    if from_user.id == to_user.id and to_user.badge_setting == "unlistened":
        to_user.badge_num += 1
        send_push_message(to_user.device_token, badge_num=to_user.badge_num)

    

    db.session.add(to_user)
    db.session.commit()
        

    return jsonify(orm_queue_item.dictify())

def get_user(user_id):
    return db.session.query(User).get(user_id)

def fb_user_is_valid(fb_id, access_token):
    resp = requests.get("%s/me?access_token=%s" % (FB_API_URL, access_token))

    if resp.status_code != 200:
        return False

    if resp.json()['id'] != fb_id:
        return False
    
    return True

def get_user_by_fbid(fb_id):
    
    users = list(db.session.query(User).filter(User.fb_id == fb_id))

    if not users:
        return None

    return users[0]

def no_such_user(user_id):

    return jsonify({"message":"no such user %s" % user_id}), 404

def is_friends(user_id_1, user_id_2, access_token):
    if user_id_1 == user_id_2:
        return True

    resp = requests.get(
        "%s/%s/friends/%s?access_token=%s" %
        (FB_API_URL, user_id_1, user_id_2, access_token))

    if resp.status_code != 200 or resp.json()['data'] == []:
        return False

    return True

def recalc_badge_num(user_id):

    user = db.session.query(User).get(user_id)
    user_items = db.session.query(QueueItem).filter(QueueItem.user_id==user.id)

    if user.badge_setting == "unlistened":
        user.badge_num = sum(map(lambda x: 0 if x.listened else 1, user_items))

    if user.badge_setting == "shared":
        user.badge_num = sum(map(lambda x: 1 if not x.listened and x.queued_by_id != user.id else 0, user_items))

    if user.badge_setting == None:
        user.badge_num = 0

    db.session.add(user)
    db.session.commit()


from apnsclient import Session, Message, APNs

def send_push_message(token, message=None, badge_num=0, name=None,  item_type=None):

    con = Session.new_connection(("gateway.push.apple.com", 2195), cert_file="cert.pem", passphrase="this is the queue push key")
    message_packet = Message(token, alert=message, badge=badge_num, user=name, sound="default", itemType=item_type)

    srv = APNs(con)
    res = srv.send(message_packet)

    # Check failures. Check codes in APNs reference docs.
    for token, reason in res.failed.items():
        code, errmsg = reason

    if res.needs_retry():
        retry_message = res.retry()
        res = srv.send(retry_message)
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)


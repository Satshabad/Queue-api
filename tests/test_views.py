import os
import unittest
import tempfile
import difflib
import pprint
import json
import sys

import requests

from mock import patch, MagicMock

from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy

from queue_app import app, models, init_db, views
User = models.User
Friend = models.Friend
QueueItem = models.QueueItem
SongItem = models.SongItem
NoteItem = models.NoteItem
   

class HighLevelTests(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""

        app.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()
        self.db = SQLAlchemy(app.app)
        init_db.init_db()

        views.get_spotify_link_for_song =  MagicMock(return_value='dummylink')
        views.get_grooveshark_link=  MagicMock(return_value='dummylink')

    def tearDown(self):
        self.logout()
        pass

    def login(self, full_name, fb_id):
        views.fb_user_is_valid = MagicMock(return_value=True)
        request_json = {'accessToken':'abc', 'fbId':fb_id, 'fullName':full_name, 'imageLink':'foo'}
        resp = self.app.post('/login', data=json.dumps(request_json), content_type='application/json')
        return json.loads(resp.data)

    def logout(self):
        return self.app.get('/logout')

    def test_login(self):
        json_user = self.login('satshabad', '456')
        user = self.db.session.query(User).one()

        self.assertEqual(json_user['userID'], user.id)
        self.assertEqual(user.fb_id, 456)
        self.assertEqual(user.fullname, 'satshabad')
        self.assertEqual(user.image_link, 'foo')

        self.assertEqual(self.db.session.query(User).one().fullname, 'satshabad')
        self.assertEqual(self.db.session.query(User).one().fb_id,456)

    def test_logout_when_not_logged_in(self):
        resp =  self.app.get('/logout')
        self.assertEqual(resp.status_code, 401)

    def test_logout(self):
        views.fb_user_is_valid = MagicMock(return_value=True)
        request_json = {'accessToken':'abc', 'fbId':'456', 'fullName':'satshabad', 'imageLink':'foo'}
        resp = self.app.post('/login', data=json.dumps(request_json), content_type='application/json')

        resp =  self.app.get('/logout')

        resp =  self.app.get('/logout')
        self.assertEqual(resp.status_code, 401)


    def test_try_to_post_to_bad_user(self):
        json_user = self.login('satshabad', '456')

        item_json = {'fromUser':{'userID':json_user['userID'],'accessToken':'abc'},
                        'type':'note', 'listened':'false', 'note':{'text':'blah','images':{'small':"", 'medium':'', 'large':'', 'extraLarge':''} } }
        
        resp = self.app.post('user/%s/queue' % 4,  data=json.dumps(item_json), content_type='application/json')

        self.assertEqual(resp.status_code, 404)


    def test_try_to_make_unauthorized_post(self):
        json_user_old = self.login('satshabad', '456')
        resp = self.logout()
        json_user = self.login('fateh', '123')

        item_json = {'fromUser':{'userID':json_user_old['userID'],'accessToken':'abc'},
                        'type':'note', 'listened':'false', 'note':{'text':'blah', 'images':{'small':"", 'medium':'', 'large':'', 'extraLarge':''}}}
        
        resp = self.app.post('user/%s/queue' % json_user['userID'],  data=json.dumps(item_json),
                                content_type='application/json')

        self.assertEqual(resp.status_code, 403)
    
    @patch('queue_app.views.Linker.spotify_song')
    @patch('queue_app.views.Linker.grooveshark')
    def test_add_song_to_queue(self, spotify_song, grooveshark):
        spotify_song.return_value = "Some spotify link"
        grooveshark.return_value = "Some grooveshark link"

        json_user = self.login('satshabad', '456')

        item_json = {'fromUser':{'userID':json_user['userID'],'accessToken':'abc'},
                        'type':'song', 'listened':'false', 'song':{'name':'Too Soon to Tell','images':{'small':"", 'medium':'', 'large':'', 'extraLarge':''}, 'artist':{'name':'Todd Snider', 'images':{'small':"", 'medium':'', 'large':'', 'extraLarge':''}}, 'album':{'name':'Agnostic Hymns & Stoner Fables'}}}


        views.is_friends = MagicMock(return_value=True)
        self.app.post('user/%s/queue' % json_user['userID'], data=json.dumps(item_json), content_type='application/json')

        queue_item = self.db.session.query(QueueItem).one()

        self.assertEqual(queue_item.queued_by_user.id, json_user['userID'])
        self.assertEqual(queue_item.user.id, json_user['userID'])
        self.assertEqual(queue_item.listened, False)

        note_item = self.db.session.query(SongItem).one()

        self.assertEqual(queue_item.id, note_item.id)


    def test_add_item_to_queue(self):
        json_user = self.login('satshabad', '456')

        item_json = {'fromUser':{'userID':json_user['userID'],'accessToken':'abc'},
                        'type':'note', 'listened':'false', 'note':{'text':'blah', 'images':{'small':"", 'medium':'', 'large':'', 'extraLarge':''}}}


        views.is_friends = MagicMock(return_value=True)
        self.app.post('user/%s/queue' % json_user['userID'], data=json.dumps(item_json), content_type='application/json')

        queue_item = self.db.session.query(QueueItem).one()

        self.assertEqual(queue_item.queued_by_user.id, json_user['userID'])
        self.assertEqual(queue_item.user.id, json_user['userID'])
        self.assertEqual(queue_item.listened, False)

        note_item = self.db.session.query(NoteItem).one()

        self.assertEqual(queue_item.id, note_item.id)

    def test_get_queue(self):
        json_user = self.login('satshabad', '456')

        item_json = {'fromUser':{'userID':json_user['userID'],'accessToken':'abc'},
                        'type':'note', 'listened':'false', 'note':{'text':'blah', 'images':{'small':"", 'medium':'', 'large':'','extraLarge':'' }}}

        self.app.post('user/%s/queue' % json_user['userID'], data=json.dumps(item_json), content_type='application/json')

        resp = self.app.get('user/%s/queue' % json_user['userID'])
    
        self.assertIn("queue", resp.data)
        self.assertIn("items", resp.data)
        self.assertIn("blah", resp.data)
         

    def test_delete_item_from_queue(self):
        json_user = self.login('satshabad', '456')

        item_json = {'fromUser':{'userID':json_user['userID'],'accessToken':'abc'},
                        'type':'note', 'listened':'false', 'note':{'text':'blah', 'images':{'small':"", 'medium':'', 'large':'', 'extraLarge':''}}}

        self.app.post('user/%s/queue' % json_user['userID'], data=json.dumps(item_json), content_type='application/json')

        resp = self.app.get('user/%s/queue' % json_user['userID'])

        null = None
        queue_items = json.loads(resp.data)
        
        item_id = queue_items['queue']['items'][0]['itemId']
    
        resp = self.app.delete('user/%s/queue/%s' % (json_user['userID'], item_id))

        self.assertEqual(self.db.session.query(QueueItem).all(), [])
        self.assertEqual(self.db.session.query(NoteItem).all(), [])

    def test_additem_to_queue_by_fbid(self):
        json_user = self.login('satshabad', '456')

        item_json = {'fromUser':{'userID':json_user['userID'],'accessToken':'abc'},
                        'type':'note', 'listened':'false', 'note':{'text':'blah', 'images':{'small':"", 'medium':'', 'large':'', 'extraLarge':''}}}

        self.app.post('fbuser/%s/queue' % 123, data=json.dumps(item_json), content_type='application/json')

        queue_item = self.db.session.query(QueueItem).one()

        self.assertEqual(queue_item.queued_by_user.id, json_user['userID'])
        self.assertEqual(queue_item.user.fb_id, 123)
        self.assertEqual(self.db.session.query(User).filter(User.fb_id==456).one().fb_id, 456)

    def test_mark_item_listened(self):
        json_user = self.login('satshabad', '456')

        item_json = {'fromUser':{'userID':json_user['userID'],'accessToken':'abc'},
                        'type':'note', 'listened':'false', 'note':{'text':'blah', 'images':{'small':"", 'medium':'', 'large':'', 'extraLarge':''}}}

        self.app.post('user/%s/queue' % json_user['userID'], data=json.dumps(item_json), content_type='application/json')
        resp = self.app.get('user/%s/queue' % json_user['userID'])

        null = None
        queue_items = json.loads(resp.data)
        
        item_id = queue_items['queue']['items'][0]['itemId']
    
        item_json['listened'] = 'true'
 
        resp = self.app.put('user/%s/queue/%s' % (json_user['userID'], item_id),
                            data=json.dumps(item_json), content_type='application/json')

        self.assertEqual(self.db.session.query(QueueItem).one().listened, True)

    def test_add_lastfm_user_name(self):
        json_user = self.login('satshabad', '456')

        data = {'lastFMUsername':'satshabad'}
        resp = self.app.put('user/%s' % json_user['userID'], data=json.dumps(data), content_type='application/json')
        self.assertEqual(json.loads(resp.data)['userID'], json_user['userID'])
        self.assertEqual(self.db.session.query(User).one().lastfm_name, 'satshabad')

    def test_return_404_for_bad_queue_item(self):
        json_user = self.login('satshabad', '456')


        resp = self.app.delete('user/%s/queue/1' % json_user['userID'])

        self.assertEqual(resp.status_code, 404)
    
    @patch('queue_app.views.requests', MagicMock())
    @patch('queue_app.views.LastFMer')
    def test_get_listens(self, LastFMer):

        json_user = self.login('satshabad', '456')

        data = {'lastFMUsername':'satshabad'}
        resp = self.app.put('user/%s' % json_user['userID'], data=json.dumps(data), content_type='application/json')
        LastFMer.get_user_listens.return_value = {'tracks':[]}
        resp = self.app.get('user/%s/listens' % json_user['userID'])

 


if __name__ == '__main__':
    unittest.main()

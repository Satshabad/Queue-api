import os
import unittest
import tempfile
import difflib
import pprint
import json
import sys

from mock import patch, MagicMock

from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy

from queue_app import main, models, init_db, queueapi
User = models.User
Friend = models.Friend
QueueItem = models.QueueItem
NoteItem = models.NoteItem
   

class QueueAPITestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""

        self.db_fd, self.db_file = tempfile.mkstemp()
        main.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % self.db_file
        main.app.config['TESTING'] = True
        self.app = main.app.test_client()
        self.db = SQLAlchemy(main.app)
        init_db.init_db()

        queueapi.get_fb_friends =  MagicMock(return_value=[{'name':'bob', 'id':'123'}])
        queueapi.get_spotify_link_for_song =  MagicMock(return_value='dummylink')

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_file)

    def test_create_user(self):
        request_json = {'accessToken':'abc', 'fbId':'456', 'fullname':'satshabad', 'imageLink':'foo'}

        resp = self.app.post('/satshabad', data=json.dumps(request_json), content_type='application/json')

        user = self.db.session.query(User).one()

        self.assertEqual(user.uname, 'satshabad')
        self.assertEqual(user.access_token, 'abc')
        self.assertEqual(user.fb_id, 456)
        self.assertEqual(user.fullname, 'satshabad')
        self.assertEqual(user.image_link, 'foo')

        friend = self.db.session.query(Friend).one()

        self.assertEqual(friend.user.uname, 'satshabad')
        self.assertEqual(friend.fb_id, 123)

    def test_add_item_to_queue(self):
        user_json = {'accessToken':'abc', 'fbId':'456', 'fullname':'satshabad', 'imageLink':'foo'}

        self.app.post('/satshabad', data=json.dumps(user_json), content_type='application/json')

        item_json = {'fromUser':{'userName':'satshabad','accessToken':'abc'}, 'type':'note', 'note':{'text':'blah'}}

        self.app.post('/satshabad/queue', data=json.dumps(item_json), content_type='application/json')

        queue_item = self.db.session.query(QueueItem).one()

        self.assertEqual(queue_item.queued_by_user.uname, 'satshabad')
        self.assertEqual(queue_item.user.uname, 'satshabad')
        self.assertEqual(queue_item.listened, False)

        note_item = self.db.session.query(NoteItem).one()

        self.assertEqual(queue_item.id, note_item.id)

    def test_get_queue(self):
        user_json = {'accessToken':'abc', 'fbId':'456', 'fullname':'satshabad', 'imageLink':'foo'}

        self.app.post('/satshabad', data=json.dumps(user_json), content_type='application/json')

        item_json = {'fromUser':{'userName':'satshabad','accessToken':'abc'}, 'type':'note', 'note':{'text':'blah'}}

        self.app.post('/satshabad/queue', data=json.dumps(item_json), content_type='application/json')

        resp = self.app.get('/satshabad/queue')
    
        self.assertIn("queue", resp.data)
        self.assertIn("items", resp.data)
        self.assertIn("blah", resp.data)

         

    def test_delete_item_from_queue(self):
        user_json = {'accessToken':'abc', 'fbId':'456', 'fullname':'satshabad', 'imageLink':'foo'}

        self.app.post('/satshabad', data=json.dumps(user_json), content_type='application/json')

        item_json = {'fromUser':{'userName':'satshabad','accessToken':'abc'}, 'type':'note', 'note':{'text':'blah'}}

        self.app.post('/satshabad/queue', data=json.dumps(item_json), content_type='application/json')

        resp = self.app.get('/satshabad/queue')

        null = None

        rv = json.loads(resp.data)
        
        item_id = rv['queue']['items'][0]['itemId']
    
        resp = self.app.delete('/satshabad/queue/%s?accessToken=abc' % item_id)

        self.assertEqual(self.db.session.query(QueueItem).all(), [])
        self.assertEqual(self.db.session.query(NoteItem).all(), [])

    def test_mark_item_listened(self):
        user_json = {'accessToken':'abc', 'fbId':'456', 'fullname':'satshabad', 'imageLink':'foo'}

        self.app.post('/satshabad', data=json.dumps(user_json), content_type='application/json')

        item_json = {'fromUser':{'userName':'satshabad','accessToken':'abc'}, 'type':'note', 'note':{'text':'blah'}}

        self.app.post('/satshabad/queue', data=json.dumps(item_json), content_type='application/json')

        resp = self.app.get('/satshabad/queue')

        null = None

        rv = json.loads(resp.data)
        
        item_id = rv['queue']['items'][0]['itemId']

        resp = self.app.put('/satshabad/queue/%s?listened=true&accessToken=abc' % item_id)

        self.assertEqual(self.db.session.query(QueueItem).one().listened, True)

if __name__ == '__main__':
    unittest.main()

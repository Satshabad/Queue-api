import os
import unittest
import tempfile
import difflib
import pprint
import json
import sys

import requests
from expecter import expect

from mock import patch, MagicMock

from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy

from queue_app import app, models, init_db, views, feedback
User = models.User
Friend = models.Friend
QueueItem = models.QueueItem
SongItem = models.SongItem
NoteItem = models.NoteItem
 
def make_user_post_dict(fb_id=456, full_name='satshabad', 
                        access_token='abc', 
                        image_link='http://image.com/jpeg',
                        device_token="098876765",
                        badge_setting=None):

    return {'accessToken':access_token, 
            'fbId':fb_id, 
            'fullName':full_name, 
            'imageLink':image_link, 
            "deviceToken":device_token,
            "badgeSetting":badge_setting}

def make_note_post_dict(user_id, access_token, listened=False, text='blah'):
    return {'fromUser':{'userID':user_id, 'accessToken':access_token},
            'type':'note', 'listened':listened, 
            'note':{'text':text,'images':{'small':'', 'medium':'', 'large':'', 'extraLarge':''} } }

def make_song_post_dict(user_id, access_token, listened=False, song_name="Too Soon To Tell", artist="Todd Snider", album="Agnostic Hymns & Stoner Fables"):
        return {'fromUser':{'userID':user_id,'accessToken':access_token},
                        'type':'song', 'listened':listened, 'song':{'name':song_name,'images':{'small':"", 'medium':'', 'large':'', 'extraLarge':''}, 'artist':{'name':artist, 'images':{'small':"", 'medium':'', 'large':'', 'extraLarge':''}}, 'album':{'name':album}}}



class TestView(unittest.TestCase):
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

    @patch('queue_app.views.fb_user_is_valid')
    def login(self, user_dict, fb_user_is_valid):
        fb_user_is_valid.return_value = True
        resp = self.app.post('/login', data=json.dumps(user_dict), content_type='application/json')
        return json.loads(resp.data)

    def login_and_get_user_id(self, user_dict):
        return self.login(user_dict)['userID']

    def logout(self):
        return self.app.get('/logout')

    @patch('queue_app.feedback.Session')
    @patch('queue_app.feedback.APNs')
    def it_removes_invalid_tokens(self, APNs, Session):
        self.db.session.add(models.User(fb_id=123, device_token=456))
        self.db.session.add(models.User(fb_id=124, device_token=789))
        self.db.session.commit()

        APNs.return_value.feedback.return_value = [(456, "blah"),(789, "blah")]

        feedback.remove_tokens()
        user_1 = self.db.session.query(models.User).get(1) 
        user_2 = self.db.session.query(models.User).get(2)
        expect(user_1.device_token) == None
        expect(user_2.device_token) == None


class TestLogin(TestView):

    def it_logs_the_user_in(self):
        user_dict = make_user_post_dict()
        user_id = self.login_and_get_user_id(user_dict)

        user = self.db.session.query(User).one()

        self.assertEqual(user_id, user.id)
        self.assertEqual(user.fb_id, user_dict['fbId'])
        self.assertEqual(user.fullname, user_dict['fullName'])
        self.assertEqual(user.image_link, user_dict['imageLink'])

    def it_returns_401_when_logging_out_if_not_logged_in(self):
        resp =  self.app.get('/logout')

        expect(resp.status_code) == 401

    def it_logs_out_a_logged_in_user(self):
        user_dict = make_user_post_dict()
        user_response = self.login(user_dict)

        resp =  self.app.get('/logout')

        expect(resp.status_code) == 200

        resp =  self.app.get('/logout')
        expect(resp.status_code) == 401


class TestEnqueue(TestView):

    def it_returns_404_when_trying_to_enqueue_for_non_user(self):
        user_dict = make_user_post_dict()
        user_response = self.login(user_dict)
        
        note_item_dict = make_note_post_dict(user_response['userID'], user_dict['accessToken'])
         
        resp = self.app.post('user/%s/queue' % user_response['userID'] + str(1),  data=json.dumps(note_item_dict), content_type='application/json')

        expect(resp.status_code) == 404

    def it_returns_401_when_the_user_is_not_logged_in(self):

        user_dict = make_user_post_dict()
        user_id = self.login_and_get_user_id(user_dict)
        resp = self.logout()

        item_dict = make_note_post_dict(user_id, user_dict['accessToken'])
        
        resp = self.app.post('user/%s/queue' % user_id,  data=json.dumps(item_dict),
                                content_type='application/json')

        expect(resp.status_code) == 401


    @patch('queue_app.views.is_friends')
    def it_returns_403_when_user_is_unauthorized(self, is_friends):

        is_friends.return_value = True

        user_dict_1 = make_user_post_dict()
        user_id_1 = self.login_and_get_user_id(user_dict_1)

        resp = self.logout()

        user_dict_2 = make_user_post_dict(full_name='fateh', access_token='xyz', fb_id=984)
        user_id_2 = self.login_and_get_user_id(user_dict_2)

        item_dict = make_note_post_dict(user_id_1, user_dict_1['accessToken'])
        
        resp = self.app.post('user/%s/queue' % user_id_1,  data=json.dumps(item_dict),
                                content_type='application/json')

        expect(resp.status_code) == 403

    @patch('queue_app.views.is_friends')
    def it_returns_403_when_two_users_are_not_friends(self, is_friends):

        is_friends.return_value = False

        user_dict_1 = make_user_post_dict()
        user_id_1 = self.login_and_get_user_id(user_dict_1)

        resp = self.logout()

        user_dict_2 = make_user_post_dict(full_name='fateh', access_token='xyz', fb_id=984)
        user_id_2 = self.login_and_get_user_id(user_dict_2)

        item_dict = make_note_post_dict(user_id_2, user_dict_2['accessToken'])
        
        resp = self.app.post('user/%s/queue' % user_id_1,  data=json.dumps(item_dict),
                                content_type='application/json')

        expect(resp.status_code) == 403

    
    @patch('queue_app.views.Linker.grooveshark')
    @patch('queue_app.views.is_friends')
    @patch('queue_app.views.Linker.spotify_song')
    def it_adds_a_song_to_my_queue(self, spotify_song, is_friends, grooveshark):
        spotify_song.return_value = "Some spotify link"
        grooveshark.return_value = "Some grooveshark link"
        is_friends.return_value = True

        user_dict = make_user_post_dict()
        user_id = self.login_and_get_user_id(user_dict)
        song_dict = make_song_post_dict(user_id, user_dict['accessToken'])

        self.app.post('user/%s/queue' % user_id, data=json.dumps(song_dict), content_type='application/json')

        queue_item = self.db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == user_id 
        expect(queue_item.user.id) == user_id 
        expect(queue_item.listened) == False
        expect(queue_item.urls.grooveshark_url) ==  "Some grooveshark link"
        expect(queue_item.urls.spotify_url) == "Some spotify link"

        song_item = self.db.session.query(SongItem).one()
        expect(queue_item.id) == song_item.id
        expect(song_item.name) == song_dict['song']['name']

        expect(song_item.artist.name) == song_dict['song']['artist']['name']
        expect(song_item.album.name) == song_dict['song']['album']['name']

    @patch('queue_app.views.Linker.grooveshark')
    @patch('queue_app.views.is_friends')
    @patch('queue_app.views.Linker.spotify_song')
    def it_adds_a_song_to_my_friends_queue(self, spotify_song, is_friends, grooveshark):
        spotify_song.return_value = "Some spotify link"
        grooveshark.return_value = "Some grooveshark link"
        is_friends.return_value = True

        user_dict_other = make_user_post_dict()
        user_id_other = self.login_and_get_user_id(user_dict_other)

        self.logout()

        user_dict = make_user_post_dict()
        user_dict['fbId'] = 3666635
        user_id = self.login_and_get_user_id(user_dict)
        song_dict = make_song_post_dict(user_id, user_dict['accessToken'])
        self.app.post('user/%s/queue' % user_id_other, data=json.dumps(song_dict), content_type='application/json')

        queue_item = self.db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == user_id 
        expect(queue_item.user.id) == user_id_other
        expect(queue_item.listened) == False
        expect(queue_item.urls.grooveshark_url) ==  "Some grooveshark link"
        expect(queue_item.urls.spotify_url) == "Some spotify link"

        song_item = self.db.session.query(SongItem).one()
        expect(queue_item.id) == song_item.id
        expect(song_item.name) == song_dict['song']['name']

        expect(song_item.artist.name) == song_dict['song']['artist']['name']
        expect(song_item.album.name) == song_dict['song']['album']['name']

    @patch('queue_app.views.is_friends')
    def it_adds_a_note_to_my_queue(self, is_friends):

        is_friends.return_value = True

        user_dict = make_user_post_dict()
        user_id = self.login_and_get_user_id(user_dict)
        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])


        self.app.post('user/%s/queue' %  user_id, data=json.dumps(note_dict), content_type='application/json')

        queue_item = self.db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == user_id 
        expect(queue_item.user.id) == user_id 
        expect(queue_item.listened) == False
        expect(queue_item.urls.grooveshark_url) ==  None
        expect(queue_item.urls.spotify_url) == None

        note_item = self.db.session.query(NoteItem).one()
        expect(queue_item.id) == note_item.id
        expect(note_item.text) == note_dict['note']['text']

    @patch('queue_app.views.is_friends')
    def it_adds_an_item_by_facebook_id(self, is_friends):

        is_friends.return_value = True

        user_dict = make_user_post_dict(fb_id=123)
        user_id = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])

        resp = self.app.post('fbuser/%s/queue' % user_dict['fbId'], data=json.dumps(note_dict), content_type='application/json')

        expect(resp.status_code) == 200

        queue_item = self.db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == user_id
        expect(queue_item.user.fb_id) == user_dict['fbId']

    @patch('queue_app.views.is_friends')
    @patch('queue_app.views.send_push_message')
    def it_sends_push_messages_for_unlistened_adding(self, send_push_message, is_friends):
        is_friends.return_value = True
        user_dict = make_user_post_dict(badge_setting="unlistened")
        user_id = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])


        resp = self.app.post('user/%s/queue' % user_id, data=json.dumps(note_dict), content_type='application/json')

        orm_user = self.db.session.query(User).one()
        expect(orm_user.badge_num) == 1

        send_push_message.assert_called_once_with(user_dict["deviceToken"], badge_num=1)

    @patch('queue_app.views.send_push_message')
    @patch('queue_app.views.Linker.grooveshark')
    @patch('queue_app.views.is_friends')
    @patch('queue_app.views.Linker.spotify_song')
    def it_sends_push_messages_for_shared_addding(self, spotify_song, is_friends, grooveshark, send_push_message):
        spotify_song.return_value = "Some spotify link"
        grooveshark.return_value = "Some grooveshark link"
        is_friends.return_value = True

        user_dict = make_user_post_dict(badge_setting="shared")
        user_id = self.login_and_get_user_id(user_dict)

        self.logout

        user_dict_other = make_user_post_dict(fb_id=7657567)
        user_id_other = self.login_and_get_user_id(user_dict_other)


        note_dict = make_note_post_dict(user_id_other, user_dict_other['accessToken'])


        resp = self.app.post('user/%s/queue' % user_id, data=json.dumps(note_dict), content_type='application/json')
        orm_user = self.db.session.query(User).get(user_id)
        expect(orm_user.badge_num) == 1

        send_push_message.assert_called_once_with(user_dict_other['deviceToken'], message='%s shared a note with you' % user_dict_other['fullName'], badge_num=1, name=user_dict_other['fullName'], item_type='note')

    @patch('queue_app.views.send_push_message')
    @patch('queue_app.views.Linker.grooveshark')
    @patch('queue_app.views.is_friends')
    @patch('queue_app.views.Linker.spotify_song')
    def it_dosent_send_push_messages_for_non_shared_addding(self, spotify_song, is_friends, grooveshark, send_push_message):
        spotify_song.return_value = "Some spotify link"
        grooveshark.return_value = "Some grooveshark link"
        is_friends.return_value = True

        user_dict = make_user_post_dict(badge_setting="shared")
        user_id = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])

        resp = self.app.post('user/%s/queue' % user_id, data=json.dumps(note_dict), content_type='application/json')
        orm_user = self.db.session.query(User).get(user_id)
        expect(orm_user.badge_num) == 0

        expect(send_push_message.called) == False


class TestGetQueue(TestView):

    def it_returns_the_queue_in_the_right_order(self):
        user_dict = make_user_post_dict()
        user_id = self.login_and_get_user_id(user_dict)

        note_dict_1 = make_note_post_dict(user_id, user_dict['accessToken'], text="item 1")
        note_dict_2 = make_note_post_dict(user_id, user_dict['accessToken'], text="item 2")
        note_dict_3 = make_note_post_dict(user_id, user_dict['accessToken'], text="item 3")

        self.app.post('user/%s/queue' % user_id,  data=json.dumps(note_dict_1), content_type='application/json')
        self.app.post('user/%s/queue' % user_id,  data=json.dumps(note_dict_2), content_type='application/json')
        self.app.post('user/%s/queue' % user_id,  data=json.dumps(note_dict_3), content_type='application/json')

        note_item_3 = self.db.session.query(NoteItem).filter(NoteItem.text == "item 3").one()
        note_item_3.queue_item.date_queued = 1000
        self.db.session.add(note_item_3)
        self.db.session.commit()

        note_item_2 = self.db.session.query(NoteItem).filter(NoteItem.text == "item 2").one()
        note_item_2.queue_item.listened = True 
        self.db.session.add(note_item_2)
        self.db.session.commit()

        resp = self.app.get('user/%s/queue' % user_id)

        data = json.loads(resp.data)
        expect(data).contains("queue")
        expect(data["queue"]).contains("items")

        expect(data["queue"]['items'][0]['note']['text']) == "item 1"
        expect(data["queue"]['items'][1]['note']['text']) == "item 3"
        expect(data["queue"]['items'][2]['note']['text']) == "item 2"

   
class TestDeleteQueueItem(TestView):

    def it_deletes_an_items_from_the_queue(self):

        user_dict = make_user_post_dict()
        user_id = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])

        resp = self.app.post('user/%s/queue' % user_id,  data=json.dumps(note_dict), content_type='application/json')
        print resp        

        
        note_item_id = self.db.session.query(QueueItem).one().id

        resp = self.app.delete('user/%s/queue/%s' % (user_id, note_item_id))

        expect(self.db.session.query(QueueItem).all()) == []
        expect(self.db.session.query(NoteItem).all()) == []

    def it_returns_403_when_tries_to_delete_someone_elses_item(self):

        user_dict = make_user_post_dict()
        user_id_1 = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id_1, user_dict['accessToken'])

        self.app.post('user/%s/queue' % user_id_1,  data=json.dumps(note_dict), content_type='application/json')
    
        self.logout()

        user_dict = make_user_post_dict(fb_id=908, full_name='fateh', access_token='xyz')
        user_id_2 = self.login_and_get_user_id(user_dict)
        
        note_item_id = self.db.session.query(QueueItem).one().id

        resp = self.app.delete('user/%s/queue/%s' % (user_id_1, note_item_id))

        expect(resp.status_code) == 403
        expect(len(self.db.session.query(QueueItem).all())) == 1
    

    @patch('queue_app.views.send_push_message')
    def it_sends_push_with_new_badge_number_for_unlistened(self, send_push_message):
        user_dict = make_user_post_dict(badge_setting="unlistened")
        user_id = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])

        self.app.post('user/%s/queue' % user_id,  data=json.dumps(note_dict), content_type='application/json')
    
        
        note_item_id = self.db.session.query(QueueItem).one().id
        orm_user = self.db.session.query(User).one()
        
        expect(orm_user.badge_num) == 1

        send_push_message.reset_mock()
        resp = self.app.delete('user/%s/queue/%s' % (user_id, note_item_id))

        expect(self.db.session.query(QueueItem).all()) == []
        expect(self.db.session.query(NoteItem).all()) == []

        orm_user = self.db.session.query(User).one()
        expect(orm_user.badge_num) == 0
        send_push_message.assert_called_once_with(user_dict['deviceToken'], badge_num=orm_user.badge_num)

    @patch('queue_app.views.send_push_message')
    def it_doesnt_send_push_with_new_badge_number_for_shared(self, send_push_message):
        user_dict = make_user_post_dict(badge_setting="shared")
        user_id = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])

        self.app.post('user/%s/queue' % user_id,  data=json.dumps(note_dict), content_type='application/json')
    
        note_item_id = self.db.session.query(QueueItem).one().id
        orm_user = self.db.session.query(User).one()
        
        expect(orm_user.badge_num) == 0

        send_push_message.reset_mock()
        resp = self.app.delete('user/%s/queue/%s' % (user_id, note_item_id))

        expect(self.db.session.query(QueueItem).all()) == []
        expect(self.db.session.query(NoteItem).all()) == []

        orm_user = self.db.session.query(User).one()
        expect(orm_user.badge_num) == 0
        expect(send_push_message.called) == False

    @patch('queue_app.views.send_push_message')
    def it_doesnt_send_push_with_new_badge_number_when_already_listened(self, send_push_message):
        user_dict = make_user_post_dict(badge_setting="unlistened")
        user_id = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])

        self.app.post('user/%s/queue' % user_id,  data=json.dumps(note_dict), content_type='application/json')
    

        orm_user = self.db.session.query(User).one()

        expect(orm_user.badge_num) == 1

        note_item = self.db.session.query(QueueItem).one()
        note_item.listened = True
        self.db.session.add(note_item)
        self.db.session.commit()

        send_push_message.reset_mock()
        resp = self.app.delete('user/%s/queue/%s' % (user_id, note_item.id))

        orm_user = self.db.session.query(User).one()
        expect(orm_user.badge_num) == 1
        expect(send_push_message.called) == False


class TestUpdateQueueItem(TestView):

    def it_returns_403_when_tries_to_update_someone_elses_item(self):
        user_dict = make_user_post_dict()
        user_id = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])

        resp = self.app.post('user/%s/queue' % user_id, data=json.dumps(note_dict), content_type='application/json')
        self.logout() 
        user_dict_2 = make_user_post_dict(fb_id=908, full_name='fateh', access_token='xyz')
        self.login(user_dict_2)

        item_id = json.loads(resp.data)['itemId'] 
        note_dict['listened'] = 1
        
        resp = self.app.put('user/%s/queue/%s' % (user_id, item_id),  data=json.dumps(note_dict), content_type='application/json')

        expect(resp.status_code) == 403
        expect(self.db.session.query(QueueItem).get(item_id).listened) == False

    def it_marks_an_item_as_listened(self):
        user_dict = make_user_post_dict()
        user_id = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])

        resp = self.app.post('user/%s/queue' % user_id, data=json.dumps(note_dict), content_type='application/json')

        item_id = json.loads(resp.data)['itemId'] 
        note_dict['listened'] = 1
        
        self.app.put('user/%s/queue/%s' % (user_id, item_id),  data=json.dumps(note_dict), content_type='application/json')

        note_item_id = self.db.session.query(QueueItem).one().id

        expect(self.db.session.query(QueueItem).get(note_item_id).listened) == True

    @patch('queue_app.views.send_push_message')
    def it_sends_a_push_notification_when_set_to_listen(self, send_push_message):
        user_dict = make_user_post_dict(badge_setting="unlistened")
        user_id = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])

        resp = self.app.post('user/%s/queue' % user_id, data=json.dumps(note_dict), content_type='application/json')

        orm_user = self.db.session.query(User).one()
        expect(orm_user.badge_num) == 1

        item_id = json.loads(resp.data)['itemId'] 
        note_dict['listened'] = 1
        

        send_push_message.reset_mock()
        self.app.put('user/%s/queue/%s' % (user_id, item_id),  data=json.dumps(note_dict), content_type='application/json')

        orm_user = self.db.session.query(User).one()

        expect(orm_user.badge_num) == 0
        send_push_message.assert_called_once_with(user_dict['deviceToken'], badge_num=0)

    @patch('queue_app.views.send_push_message')
    def it_sends_push_notification_when_set_to_not_listened(self, send_push_message):
        user_dict = make_user_post_dict(badge_setting="unlistened")
        user_id = self.login_and_get_user_id(user_dict)

        note_dict = make_note_post_dict(user_id, user_dict['accessToken'])

        resp = self.app.post('user/%s/queue' % user_id, data=json.dumps(note_dict), content_type='application/json')

        orm_user = self.db.session.query(User).one()
        expect(orm_user.badge_num) == 1

        orm_note = self.db.session.query(QueueItem).one()
        orm_note.listened = True
        self.db.session.add(orm_note)
        self.db.session.commit()

        item_id = json.loads(resp.data)['itemId'] 
        note_dict['listened'] = 0
        

        send_push_message.reset_mock()
        self.app.put('user/%s/queue/%s' % (user_id, item_id),  data=json.dumps(note_dict), content_type='application/json')

        orm_user = self.db.session.query(User).one()

        expect(orm_user.badge_num) == 2
        send_push_message.assert_called_once_with(user_dict['deviceToken'], badge_num=2)



class TestUpdateUser(TestView):

    def it_returns_403_when_updating_a_different_user(self):
        user_dict_1 = make_user_post_dict()
        user_id_1 = self.login_and_get_user_id(user_dict_1)

        self.logout() 
        user_dict_2 = make_user_post_dict(fb_id=908, full_name='fateh', access_token='xyz')
        self.login(user_dict_2)

        user_dict_1['lastFMUsername'] = 'satshabad'

        resp = self.app.put('user/%s' % user_id_1,  data=json.dumps(user_dict_1), content_type='application/json')
        expect(resp.status_code) == 403

    def it_adds_the_last_fm_name_to_the_user(self):
        user_dict = make_user_post_dict()
        user_id = self.login_and_get_user_id(user_dict)

        user_dict['lastFMUsername'] = 'ssk'

        resp = self.app.put('user/%s' % user_id,  data=json.dumps(user_dict), content_type='application/json')

        expect(resp.status_code) == 200
        expect(self.db.session.query(User).one().lastfm_name) == "ssk"


if __name__ == '__main__':
    unittest.main()

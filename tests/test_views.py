import json
import os
import unittest
import inspect
from pprint import pprint

import requests
import vcr

from expecter import expect
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, request
from mock import patch, MagicMock

from api import app, init_db, views, feedback
from api import fixtures
from api.fixtures import (make_user,
                          make_song_from,
                          make_note_from,
                          make_artist_from)

from api.models import (User,
                        Friend,
                        QueueItem,
                        SongItem,
                        NoteItem,
                        ArtistItem,
                        Artist)

vcr = vcr.VCR(
    cassette_library_dir='fixtures/vcr_cassettes'
)


def function_name():
    return inspect.stack()[1][3]


class TestView(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""

        app.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()
        self.db = SQLAlchemy(app.app)
        init_db.init_db()

        global satshabad
        global fateh
        satshabad = fixtures.make_user("satshabad")
        fateh = fixtures.make_user("fateh")

    def tearDown(self):

        self.logout()

    @patch('api.views.fb_user_is_valid')
    def login(self, user, fb_user_is_valid):
        fb_user_is_valid.return_value = True

        resp = self.app.post(
            '/login',
            data=json.dumps(user),
            content_type='application/json')

        return json.loads(resp.data), json.loads(resp.data)['userID']

    def logout(self):
        return self.app.get('/logout')


class TestLogin(TestView):

    def it_logs_the_user_in(self):
        user, uid = self.login(satshabad)

        resp = self.app.get('/logout')

        expect(resp.status_code) == 200

        user, uid = self.login(satshabad)

    def it_logs_the_user_in_for_the_first_time(self):
        user, uid = self.login(satshabad)

        db_user = self.db.session.query(User).one()

        expect(db_user.id) == uid
        expect(db_user.fb_id) == user['fbId']
        expect(db_user.fullname) == user['fullName']
        expect(db_user.image_link) == user['imageLink']

    def it_returns_401_when_logging_out_if_not_logged_in(self):
        resp = self.app.get('/logout')

        expect(resp.status_code) == 401

    def it_logs_out_a_logged_in_user(self):
        user, uid = self.login(satshabad)

        resp = self.app.get('/logout')

        expect(resp.status_code) == 200

        resp = self.app.get('/logout')
        expect(resp.status_code) == 401


class TestEnqueue(TestView):

    def it_returns_404_when_enqueuing_for_other_user(self):
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        resp = self.app.post(
            'user/%s/queue' % str(100),
            data=json.dumps(song),
            content_type='application/json')

        expect(resp.status_code) == 404

    def it_returns_401_when_the_user_is_not_logged_in(self):
        user, uid = self.login(satshabad)

        resp = self.logout()

        song = make_song_from(user)

        resp = self.app.post(
            'user/%s/queue' % uid, data=json.dumps(song),
            content_type='application/json')

        expect(resp.status_code) == 401

    @patch('api.views.is_friends')
    def it_returns_403_when_user_is_unauthorized(self, is_friends):

        is_friends.return_value = True

        user1, uid1 = self.login(satshabad)
        resp = self.logout()

        user2, uid2 = self.login(fateh)

        song = make_song_from(user1)

        resp = self.app.post(
            'user/%s/queue' % uid1, data=json.dumps(song),
            content_type='application/json')

        expect(resp.status_code) == 403

    @patch('api.views.is_friends')
    def it_returns_403_when_two_users_are_not_friends(self, is_friends):

        is_friends.return_value = False

        user1, uid1 = self.login(satshabad)
        resp = self.logout()

        user2, uid2 = self.login(fateh)

        song = make_song_from(user1)

        resp = self.app.post(
            'user/%s/queue' % uid1, data=json.dumps(song),
            content_type='application/json')

        expect(resp.status_code) == 403

    @patch('api.views.is_friends')
    def it_adds_a_song_to_my_queue(self, is_friends):
        is_friends.return_value = True

        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

        expect(resp.status_code) == 200

        queue_item = self.db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == uid
        expect(queue_item.user.id) == uid
        expect(queue_item.listened) == False
        expect(queue_item.urls.grooveshark_url) is not None
        expect(queue_item.urls.spotify_url) is not None

        song_item = self.db.session.query(SongItem).one()
        expect(queue_item.id) == song_item.id
        expect(song_item.name) == song['song']['name']

        expect(song_item.artist.name) == song['song']['artist']['name']
        expect(song_item.album.name) == song['song']['album']['name']

    @patch('api.views.is_friends')
    def it_adds_a_note_to_my_queue(self, is_friends):

        is_friends.return_value = True

        user, uid = self.login(satshabad)
        note = make_note_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid,
                data=json.dumps(note),
                content_type='application/json')

        expect(resp.status_code) == 200

        queue_item = self.db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == uid
        expect(queue_item.user.id) == uid
        expect(queue_item.listened) == False
        expect(queue_item.urls.grooveshark_url) is None
        expect(queue_item.urls.spotify_url) is None

        note_item = self.db.session.query(NoteItem).one()
        expect(queue_item.id) == note_item.id
        expect(note_item.text) == note['note']['text']

    @patch('api.views.send_push_message')
    @patch('api.views.is_friends')
    def it_adds_a_song_to_my_friends_queue(
        self, is_friends, send_push_message):

        is_friends.return_value = True

        user1, uid1 = self.login(satshabad)
        self.logout()
        user2, uid2 = self.login(fateh)

        song = make_song_from(user2)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid1,
                data=json.dumps(song),
                content_type='application/json')

        expect(resp.status_code) == 200

        queue_item = self.db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == uid2
        expect(queue_item.user.id) == uid1
        expect(queue_item.listened) == False
        expect(queue_item.urls.grooveshark_url) is not None
        expect(queue_item.urls.spotify_url) is not None

        song_item = self.db.session.query(SongItem).one()
        expect(queue_item.id) == song_item.id
        expect(song_item.name) == song['song']['name']

        expect(song_item.artist.name) == song['song']['artist']['name']
        expect(song_item.album.name) == song['song']['album']['name']

    @patch('api.views.is_friends')
    def it_adds_an_item_by_facebook_id(self, is_friends):

        is_friends.return_value = True

        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'fbuser/%s/queue' % user['fbId'],
                data=json.dumps(song),
                content_type='application/json')

        expect(resp.status_code) == 200

        queue_item = self.db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == uid
        expect(queue_item.user.fb_id) == user['fbId']


class TestPushNotifications(TestView):

    @patch('api.views.is_friends')
    @patch('api.views.send_push_message')
    def it_sends_push_messages_for_unlistened_adding(
        self, send_push_message, is_friends):
        is_friends.return_value = True

        satshabad['badgeSetting'] = 'unlistened'
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

        orm_user = self.db.session.query(User).one()
        expect(orm_user.badge_num) == 1

        send_push_message.assert_called_once_with(
            user["deviceToken"], badge_num=1)

    @patch('api.views.send_push_message')
    @patch('api.views.is_friends')
    def it_sends_push_messages_for_shared_addding(
        self, is_friends, send_push_message):
        is_friends.return_value = True

        satshabad['badgeSetting'] = 'shared'
        user1, uid1 = self.login(satshabad)
        self.logout()
        user2, uid2 = self.login(fateh)

        song = make_song_from(user2)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid1,
                data=json.dumps(song),
                content_type='application/json')

        orm_user = self.db.session.query(User).get(uid1)
        expect(orm_user.badge_num) == 1

        send_push_message.assert_called_once_with(
            user1['deviceToken'],
            message='%s shared a song with you' % user2['fullName'],
            badge_num=1,
            name=user2['fullName'],
            item_type='song')

    @patch('api.views.send_push_message')
    @patch('api.views.is_friends')
    def it_dosent_send_push_messages_for_non_shared_addding(
        self, is_friends, send_push_message):
        is_friends.return_value = True

        satshabad['badgeSetting'] = 'shared'
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

        orm_user = self.db.session.query(User).one()
        expect(orm_user.badge_num) == 0

        expect(send_push_message.called) == False

    @patch('api.views.send_push_message')
    def it_sends_push_with_new_badge_number_for_unlistened(
        self, send_push_message):
        satshabad['badgeSetting'] = 'unlistened'
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

            send_push_message.reset_mock()

            orm_user = self.db.session.query(User).one()
            song_id = self.db.session.query(QueueItem).one().id

            expect(orm_user.badge_num) == 1

            resp = self.app.delete('user/%s/queue/%s' % (uid, song_id))
            expect(resp.status_code) == 200

        orm_user = self.db.session.query(User).one()
        expect(orm_user.badge_num) == 0
        send_push_message.assert_called_once_with(
            user['deviceToken'],
            badge_num=orm_user.badge_num)

    @patch('api.views.send_push_message')
    def it_doesnt_send_push_with_new_badge_number_when_already_listened(
        self, send_push_message):

        satshabad['badgeSetting'] = 'unlistened'
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

            send_push_message.reset_mock()

            orm_user = self.db.session.query(User).one()
            song_id = self.db.session.query(QueueItem).one().id

            expect(orm_user.badge_num) == 1

            song_item = self.db.session.query(QueueItem).one()
            song_item.listened = True
            self.db.session.add(song_item)
            self.db.session.commit()

            send_push_message.reset_mock()
            resp = self.app.delete('user/%s/queue/%s' % (uid, song_id))
            expect(resp.status_code) == 200

        orm_user = self.db.session.query(User).one()
        expect(orm_user.badge_num) == 1
        expect(send_push_message.called) == False

    @patch('api.feedback.Session')
    @patch('api.feedback.APNs')
    def it_removes_invalid_tokens(self, APNs, Session):
        self.db.session.add(User(fb_id=123, device_token=456))
        self.db.session.add(User(fb_id=124, device_token=789))
        self.db.session.commit()

        APNs.return_value.feedback.return_value = [
            (456, "blah"), (789, "blah")]

        feedback.remove_tokens()
        user_1 = self.db.session.query(User).get(1)
        user_2 = self.db.session.query(User).get(2)
        expect(user_1.device_token) is None
        expect(user_2.device_token) is None

    @patch('api.views.send_push_message')
    def it_sends_a_push_notification_when_set_to_listen(self, send_push_message):
        satshabad['badgeSetting'] = 'unlistened'
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

            orm_user = self.db.session.query(User).one()
            expect(orm_user.badge_num) == 1

            song_id = json.loads(resp.data)['itemId']
            song['saved'] = 1

            send_push_message.reset_mock()

            self.app.put(
            'user/%s/queue/%s' % (uid,
             song_id),
              data=json.dumps(song),
             content_type='application/json')

        orm_user = self.db.session.query(User).one()

        expect(orm_user.badge_num) == 0
        send_push_message.assert_called_once_with(user['deviceToken'], badge_num=0)

    @patch('api.views.send_push_message')
    @patch('api.views.is_friends')
    def it_recalcs_the_badge_number_when_changed_to_unlistened(self, is_friends, send_push_message):

        is_friends.return_value = True

        satshabad['badgeSetting'] = 'shared'
        user, uid = self.login(satshabad)

        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            self.app.post('user/%s/queue' %  uid, data=json.dumps(song), content_type='application/json')
            self.app.post('user/%s/queue' %  uid, data=json.dumps(song), content_type='application/json')
            self.app.post('user/%s/queue' %  uid, data=json.dumps(song), content_type='application/json')

            user['badgeSetting'] = "unlistened"
            resp = self.app.put('user/%s' % uid,  data=json.dumps(user), content_type='application/json')

        orm_user = self.db.session.query(User).get(uid)
        expect(orm_user.badge_num) == 3

    @patch('api.views.send_push_message')
    @patch('api.views.is_friends')
    def it_recalcs_the_badge_number_when_changed_to_shared(
        self, is_friends, send_push_message):

        is_friends.return_value = True

        satshabad['badgeSetting'] = 'unlistened'
        user1, uid1 = self.login(satshabad)
        song = make_song_from(user1)

        with vcr.use_cassette(function_name() + '.yaml'):
            self.app.post(
                'user/%s/queue' % uid1,
                data=json.dumps(song),
                content_type='application/json')
            self.logout()

            user2, uid2 = self.login(fateh)
            song = make_song_from(user2)

            self.app.post(
                'user/%s/queue' % uid1,
                data=json.dumps(song),
                content_type='application/json')

            self.app.post(
                'user/%s/queue' % uid1,
                data=json.dumps(song),
                content_type='application/json')

            self.logout()

            _, _ = self.login(satshabad)

            user1['badgeSetting'] = "shared"
            resp = self.app.put(
                'user/%s' % uid1,
                data=json.dumps(user1),
                content_type='application/json')

        orm_user = self.db.session.query(User).get(uid1)
        expect(orm_user.badge_num) == 2


class TestListens(TestView):

    def it_gets_the_listens(self):
        user, uid = self.login(satshabad)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.put(
                'user/%s' % uid,
                data=json.dumps(user),
                content_type='application/json')

            resp = self.app.get('user/%s/listens' % uid)

        data = json.loads(resp.data)

        expect(data).contains('recentTracks')


class TestGetQueue(TestView):

    def it_gets_the_queue(self):
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            self.app.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

            resp = self.app.get('/user/%s/queue' % uid)

        data = json.loads(resp.data)

        expect(data).contains('queue')
        expect(data['queue']).contains('items')
        expect(len(data['queue']['items'])) == 1


class TestGetSent(TestView):

    @patch('api.views.send_push_message')
    @patch('api.views.is_friends')
    def it_gets_the_sent_items(self, is_friends, send_push_message):
        is_friends.return_value = True

        user1, uid1 = self.login(satshabad)
        self.logout()
        user2, uid2 = self.login(fateh)

        song = make_song_from(user2)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid1,
                data=json.dumps(song),
                content_type='application/json')

            resp = self.app.get('/user/%s/sent' % uid2)

        data = json.loads(resp.data)

        expect(data).contains('queue')
        expect(data['queue']).contains('items')
        expect(len(data['queue']['items'])) == 1


class TestDeleteQueueItem(TestView):

    def it_deletes_an_items_from_the_queue(self):

        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            self.app.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

            song_id = self.db.session.query(QueueItem).one().id

            resp = self.app.delete('user/%s/queue/%s' % (uid, song_id))

        expect(self.db.session.query(QueueItem).all()) == []
        expect(self.db.session.query(NoteItem).all()) == []

    def it_returns_403_when_tries_to_delete_someone_elses_item(self):

        user1, uid1 = self.login(satshabad)
        song = make_song_from(user1)

        with vcr.use_cassette(function_name() + '.yaml'):
            self.app.post(
                'user/%s/queue' % uid1,
                data=json.dumps(song),
                content_type='application/json')

            self.logout()
            user2, uid2 = self.login(fateh)

            song_id = self.db.session.query(QueueItem).one().id

            resp = self.app.delete('user/%s/queue/%s' % (uid1, song_id))

        expect(resp.status_code) == 403
        expect(len(self.db.session.query(QueueItem).all())) == 1

class TestUpdateQueueItem(TestView):

    def it_returns_403_when_tries_to_update_someone_elses_item(self):
        user1, uid1 = self.login(satshabad)
        song = make_song_from(user1)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid1, data=json.dumps(song),
                content_type='application/json')

            song_id = json.loads(resp.data)['itemId']

            self.logout()

            user2, uid2 = self.login(fateh)

            song['saved'] = 1

            resp = self.app.put(
                'user/%s/queue/%s' % (uid1, song_id),
                data=json.dumps(song),
                content_type='application/json')

        expect(resp.status_code) == 403
        expect(self.db.session.query(QueueItem).get(song_id).listened) == False

    def it_marks_an_item_as_listened(self):
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.app.post(
                'user/%s/queue' % uid, data=json.dumps(song),
                content_type='application/json')

            song_id = json.loads(resp.data)['itemId']

            song['saved'] = 1

            resp = self.app.put(
                'user/%s/queue/%s' % (uid, song_id),
                data=json.dumps(song),
                content_type='application/json')

        expect(self.db.session.query(QueueItem).get(song_id).listened)


class TestUpdateUser(TestView):

    def it_returns_403_when_updating_a_different_user(self):
        user1, uid1 = self.login(satshabad)
        song = make_song_from(user1)

        self.logout()

        user2, uid2 = self.login(fateh)

        user1['lastFMUsername'] = 'satshabad'

        resp = self.app.put(
            'user/%s' % uid1,
            data=json.dumps(song),
            content_type='application/json')

        expect(resp.status_code) == 403

    def it_adds_the_last_fm_name_to_the_user(self):
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        user['lastFMUsername'] = 'ssk'

        resp = self.app.put(
            'user/%s' % uid,
            data=json.dumps(user),
            content_type='application/json')

        expect(resp.status_code) == 200
        expect(self.db.session.query(User).one().lastfm_name) == "ssk"

    def it_adds_the_twitter_name_to_the_user(self):
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        user['twitterUsername'] = 'satshabad'

        resp = self.app.put(
            'user/%s' % uid,
            data=json.dumps(user),
            content_type='application/json')

        expect(resp.status_code) == 200
        expect(self.db.session.query(User).one().twitter_name) == "satshabad"

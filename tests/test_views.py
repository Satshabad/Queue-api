import json
import os
import inspect
from pprint import pprint

from unittest import TestCase

import requests

from expecter import expect
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, request
from mock import patch, MagicMock

from api import app, db
from api.scripts import feedback

import api
from api import fixtures
from api.fixtures import (vcr,
                          make_user,
                          make_song_from,
                          make_note_from,
                          make_artist_from,
                          function_name)

from api.models import (User,
                        Friend,
                        QueueItem,
                        SongItem,
                        NoteItem,
                        ArtistItem,
                        Artist)


class TestView(TestCase):

    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()

        global satshabad
        global fateh
        satshabad = fixtures.make_user("satshabad")
        fateh = fixtures.make_user("fateh")

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @patch('api.lib.facebook.verify')
    def login(self, user, verify):
        verify.return_value = True

        resp = self.client.post(
            '/login',
            data=json.dumps(user),
            content_type='application/json')

        return json.loads(resp.data), json.loads(resp.data)['userID']

    def logout(self):
        return self.client.get('/logout')


class TestLogin(TestView):

    def it_logs_the_user_in(self):
        user, uid = self.login(satshabad)

        resp = self.client.get('/logout')

        expect(resp.status_code) == 200

        user, uid = self.login(satshabad)

    def it_makes_a_new_user_on_login(self):
        user, uid = self.login(satshabad)

        db_user = db.session.query(User).one()

        expect(db_user.id) == uid
        expect(db_user.fb_id) == user['fbId']
        expect(db_user.fullname) == user['fullName']
        expect(db_user.image_link) == user['imageLink']

    def it_returns_401_when_logging_out_if_not_logged_in(self):
        resp = self.client.get('/logout')

        expect(resp.status_code) == 401

    def it_logs_out_a_logged_in_user(self):
        user, uid = self.login(satshabad)

        resp = self.client.get('/logout')

        expect(resp.status_code) == 200

        resp = self.client.get('/logout')
        expect(resp.status_code) == 401

    @patch('api.lib.facebook.verify')
    def it_doesnt_make_account_in_when_facebook_says_no(self, verify):
        user, uid = self.login(satshabad)
        self.logout()

        verify.return_value = False

        resp = self.client.post(
            '/login', data=json.dumps(user),
            content_type='application/json')
        expect(resp.status_code) == 403

    @patch('api.lib.facebook.verify')
    def it_doesnt_login_when_facebook_says_no(self, verify):
        verify.return_value = False
        user = satshabad

        resp = self.client.post(
            '/login', data=json.dumps(user),
            content_type='application/json')
        expect(resp.status_code) == 403

    @patch('api.lib.facebook.verify')
    def it_doesnt_log_in_without_access_token_unless_unclaimed(self, verify):
        user, uid = self.login(satshabad)
        self.logout()
        del user['accessToken']

        resp = self.client.post(
            '/login', data=json.dumps(user),
            content_type='application/json')
        expect(resp.status_code) == 403

    @patch('api.lib.facebook.verify')
    def it_doesnt_make_a_user_without_access_token(self, verify):
        user = satshabad
        del user['accessToken']

        resp = self.client.post(
            '/login', data=json.dumps(user),
            content_type='application/json')
        expect(resp.status_code) == 400

    @patch('api.views.views.assert_are_friends')
    def it_logs_in_an_anon_user_after_share(self, assert_are_friends):
        user1, uid1 = self.login(satshabad)
        user2 = fateh

        fb_id = user2['fbId']
        song = make_song_from(user1)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'fbuser/%s/queue' % fb_id, data=json.dumps(song),
                content_type='application/json')

        db_user = User.query.filter(User.fb_id == fb_id).one()
        expect(db_user.claimed) == False
        self.logout()
        del user2['accessToken']

        user2, uid2 = self.login(user2)

    @patch('api.views.views.assert_are_friends')
    def it_lets_a_user_claim_an_account_after_an_anon_share(
        self, assert_are_friends):
        user1, uid1 = self.login(satshabad)
        user2 = fateh

        fb_id = user2['fbId']
        song = make_song_from(user1)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'fbuser/%s/queue' % fb_id, data=json.dumps(song),
                content_type='application/json')

        db_user = User.query.filter(User.fb_id == fb_id).one()
        expect(db_user.claimed) == False
        self.logout()

        user2, uid2 = self.login(user2)

        db_user = User.query.filter(User.fb_id == fb_id).one()
        expect(db_user.claimed)


class TestEnqueue(TestView):

    def it_returns_404_when_enqueuing_for_other_user(self):
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        resp = self.client.post(
            'user/%s/queue' % str(100),
            data=json.dumps(song),
            content_type='application/json')

        expect(resp.status_code) == 404

    def it_returns_401_when_the_user_is_not_logged_in(self):
        user, uid = self.login(satshabad)

        resp = self.logout()

        song = make_song_from(user)

        resp = self.client.post(
            'user/%s/queue' % uid, data=json.dumps(song),
            content_type='application/json')

        expect(resp.status_code) == 401

    @patch('api.views.views.assert_are_friends')
    def it_returns_403_when_user_is_unauthorized(self, assert_are_friends):

        user1, uid1 = self.login(satshabad)
        resp = self.logout()

        user2, uid2 = self.login(fateh)

        song = make_song_from(user1)

        resp = self.client.post(
            'user/%s/queue' % uid1, data=json.dumps(song),
            content_type='application/json')

        expect(resp.status_code) == 403

    @patch('api.views.views.assert_are_friends')
    def it_returns_403_when_two_users_are_not_friends(
        self, assert_are_friends):
        assert_are_friends.side_effect = api.views.views.APIException(
            "blah", 403)
        user1, uid1 = self.login(satshabad)
        resp = self.logout()

        user2, uid2 = self.login(fateh)

        song = make_song_from(user2)

        resp = self.client.post(
            'user/%s/queue' % uid1, data=json.dumps(song),
            content_type='application/json')

        expect(resp.status_code) == 403

    @patch('api.views.views.assert_are_friends')
    def it_adds_a_song_to_my_queue(self, assert_are_friends):

        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

        expect(resp.status_code) == 200

        queue_item = db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == uid
        expect(queue_item.user.id) == uid
        expect(queue_item.listened) == False
        expect(queue_item.urls.grooveshark_url) is not None
        expect(queue_item.urls.spotify_url) is not None

        song_item = db.session.query(SongItem).one()
        expect(queue_item.id) == song_item.id
        expect(song_item.name) == song['song']['name']

        expect(song_item.artist.name) == song['song']['artist']['name']
        expect(song_item.album.name) == song['song']['album']['name']

    @patch('api.views.views.assert_are_friends')
    def it_adds_a_note_to_my_queue(self, assert_are_friends):

        user, uid = self.login(satshabad)
        note = make_note_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'user/%s/queue' % uid,
                data=json.dumps(note),
                content_type='application/json')

        expect(resp.status_code) == 200

        queue_item = db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == uid
        expect(queue_item.user.id) == uid
        expect(queue_item.listened) == False
        expect(queue_item.urls.grooveshark_url) is None
        expect(queue_item.urls.spotify_url) is None

        note_item = db.session.query(NoteItem).one()
        expect(queue_item.id) == note_item.id
        expect(note_item.text) == note['note']['text']

    @patch('api.lib.push.push')
    @patch('api.views.views.assert_are_friends')
    def it_adds_a_song_to_my_friends_queue(
        self, assert_are_friends, push):

        user1, uid1 = self.login(satshabad)
        self.logout()
        user2, uid2 = self.login(fateh)

        song = make_song_from(user2)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'user/%s/queue' % uid1,
                data=json.dumps(song),
                content_type='application/json')

        expect(resp.status_code) == 200

        queue_item = db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == uid2
        expect(queue_item.user.id) == uid1
        expect(queue_item.listened) == False
        expect(queue_item.urls.grooveshark_url) is not None
        expect(queue_item.urls.spotify_url) is not None

        song_item = db.session.query(SongItem).one()
        expect(queue_item.id) == song_item.id
        expect(song_item.name) == song['song']['name']

        expect(song_item.artist.name) == song['song']['artist']['name']
        expect(song_item.album.name) == song['song']['album']['name']

    @patch('api.views.views.assert_are_friends')
    def it_adds_an_item_by_facebook_id(self, assert_are_friends):

        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'fbuser/%s/queue' % user['fbId'],
                data=json.dumps(song),
                content_type='application/json')

        expect(resp.status_code) == 200

        queue_item = db.session.query(QueueItem).one()

        expect(queue_item.queued_by_user.id) == uid
        expect(queue_item.user.fb_id) == user['fbId']

    @patch('api.views.views.assert_are_friends')
    def it_doesnt_create_a_new_account_when_not_friends(
        self, assert_are_friends):
        assert_are_friends.side_effect = api.views.views.APIException(
            "blah", 403)
        user, uid = self.login(satshabad)

        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'fbuser/%s/queue' % str(32), data=json.dumps(song),
                content_type='application/json')

        expect(resp.status_code) == 403

    @patch('api.views.views.assert_are_friends')
    def it_creates_a_new_account_for_a_non_user(self, assert_are_friends):
        user, uid = self.login(satshabad)

        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'fbuser/%s/queue' % str(32), data=json.dumps(song),
                content_type='application/json')

        db_user = User.query.filter(User.fb_id == 32).one()
        expect(db_user.claimed) == False
        expect(QueueItem.query.filter(QueueItem.user_id == db_user.id).one())


class TestPushNotifications(TestView):

    @patch('api.views.views.assert_are_friends')
    @patch('api.lib.push.push')
    def it_sends_push_messages_for_unlistened_adding(
        self, push, assert_are_friends):

        satshabad['badgeSetting'] = 'unlistened'
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

        orm_user = db.session.query(User).one()
        expect(orm_user.badge_num) == 1

        push.assert_called_once_with(
            user['deviceToken'], None, 1, None, None)

    @patch('api.lib.push.push')
    @patch('api.views.views.assert_are_friends')
    def it_sends_push_messages_for_shared_adding(
        self, assert_are_friends, push):

        satshabad['badgeSetting'] = 'unlistened'
        user1, uid1 = self.login(satshabad)
        self.logout()
        user2, uid2 = self.login(fateh)

        song = make_song_from(user2)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'user/%s/queue' % uid1,
                data=json.dumps(song),
                content_type='application/json')

        orm_user = db.session.query(User).get(uid1)
        expect(orm_user.badge_num) == 1

        push.assert_called_once_with(
            user1['deviceToken'],
            '%s shared a song with you' % user2['fullName'],
            1,
            user2['fullName'],
            'song')

    @patch('api.lib.push.push')
    def it_sends_push_with_new_badge_number_for_unlistened(
        self, push):

        satshabad['badgeSetting'] = 'unlistened'
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

            push.reset_mock()

            orm_user = db.session.query(User).one()
            song_id = db.session.query(QueueItem).one().id

            expect(orm_user.badge_num) == 1

            resp = self.client.delete('user/%s/queue/%s' % (uid, song_id))
            expect(resp.status_code) == 200

        orm_user = db.session.query(User).one()
        expect(orm_user.badge_num) == 0

        push.assert_called_once_with(
            user['deviceToken'], None, 0, None, None)

    @patch('api.lib.push.push')
    def it_doesnt_send_push_with_new_badge_number_when_already_listened(
        self, push):

        satshabad['badgeSetting'] = 'unlistened'
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

            push.reset_mock()

            orm_user = db.session.query(User).one()
            song_id = db.session.query(QueueItem).one().id

            expect(orm_user.badge_num) == 1

            song_item = db.session.query(QueueItem).one()
            song_item.listened = True
            db.session.add(song_item)
            db.session.commit()

            push.reset_mock()
            resp = self.client.delete('user/%s/queue/%s' % (uid, song_id))
            expect(resp.status_code) == 200

        orm_user = db.session.query(User).one()
        expect(orm_user.badge_num) == 1
        expect(push.called) == False

    @patch('api.scripts.feedback.Session')
    @patch('api.scripts.feedback.APNs')
    def it_removes_invalid_tokens(self, APNs, Session):
        db.session.add(User(fb_id=123, device_token=456))
        db.session.add(User(fb_id=124, device_token=789))
        db.session.commit()

        APNs.return_value.feedback.return_value = [
            (456, "blah"), (789, "blah")]

        feedback.remove_tokens()
        user_1 = db.session.query(User).get(1)
        user_2 = db.session.query(User).get(2)
        expect(user_1.device_token) is None
        expect(user_2.device_token) is None

    @patch('api.lib.push.push')
    def it_sends_a_push_notification_when_set_to_listen(
        self, push):
        satshabad['badgeSetting'] = 'unlistened'
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

            orm_user = db.session.query(User).one()
            expect(orm_user.badge_num) == 1

            song_id = json.loads(resp.data)['itemId']
            song['saved'] = 1

            push.reset_mock()

            self.client.put(
                'user/%s/queue/%s' % (uid,
                                      song_id),
                data=json.dumps(song),
                content_type='application/json')

        orm_user = db.session.query(User).one()

        expect(orm_user.badge_num) == 0
        push.assert_called_once_with(
            user['deviceToken'], None, 0, None, None)


class TestListens(TestView):

    def it_gets_the_listens(self):
        user, uid = self.login(satshabad)
        user['lastFMUsername'] = 'satshabad'

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.put(
                'user/%s' % uid,
                data=json.dumps(user),
                content_type='application/json')

            resp = self.client.get('user/%s/listens' % uid)

        data = json.loads(resp.data)

        expect(data).contains('recentTracks')


class TestGetQueue(TestView):

    def it_gets_the_queue(self):

        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            self.client.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

            resp = self.client.get('/user/%s/queue' % uid)

        data = json.loads(resp.data)

        expect(data).contains('queue')
        expect(data['queue']).contains('items')
        expect(len(data['queue']['items'])) == 1


class TestGetSent(TestView):

    @patch('api.lib.push.push')
    @patch('api.views.views.assert_are_friends')
    def it_gets_the_sent_items(self, assert_are_friends, push):

        user1, uid1 = self.login(satshabad)
        self.logout()
        user2, uid2 = self.login(fateh)

        song = make_song_from(user2)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'user/%s/queue' % uid1,
                data=json.dumps(song),
                content_type='application/json')

            resp = self.client.get('/user/%s/sent' % uid2)

        data = json.loads(resp.data)

        expect(data).contains('queue')
        expect(data['queue']).contains('items')
        expect(len(data['queue']['items'])) == 1


class TestDeleteQueueItem(TestView):

    def it_deletes_an_item_from_the_queue(self):

        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            self.client.post(
                'user/%s/queue' % uid,
                data=json.dumps(song),
                content_type='application/json')

            song_id = db.session.query(QueueItem).one().id

            self.client.delete('user/%s/queue/%s' % (uid, song_id))
            resp = self.client.get('user/%s/queue' % uid)

        expect(db.session.query(QueueItem).one().no_show) == True

        data = json.loads(resp.data)
        expect(data['queue']['items']) == []

    def it_returns_403_when_tries_to_delete_someone_elses_item(self):

        user1, uid1 = self.login(satshabad)
        song = make_song_from(user1)

        with vcr.use_cassette(function_name() + '.yaml'):
            self.client.post(
                'user/%s/queue' % uid1,
                data=json.dumps(song),
                content_type='application/json')

            self.logout()
            user2, uid2 = self.login(fateh)

            song_id = db.session.query(QueueItem).one().id

            resp = self.client.delete('user/%s/queue/%s' % (uid1, song_id))

        expect(resp.status_code) == 403
        expect(len(db.session.query(QueueItem).all())) == 1


class TestUpdateQueueItem(TestView):

    def it_returns_403_when_tries_to_update_someone_elses_item(self):
        user1, uid1 = self.login(satshabad)
        song = make_song_from(user1)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'user/%s/queue' % uid1, data=json.dumps(song),
                content_type='application/json')

            song_id = json.loads(resp.data)['itemId']

            self.logout()

            user2, uid2 = self.login(fateh)

            song['saved'] = 1

            resp = self.client.put(
                'user/%s/queue/%s' % (uid1, song_id),
                data=json.dumps(song),
                content_type='application/json')

        expect(resp.status_code) == 403
        expect(db.session.query(QueueItem).get(song_id).listened) == False

    def it_marks_an_item_as_listened(self):
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        with vcr.use_cassette(function_name() + '.yaml'):
            resp = self.client.post(
                'user/%s/queue' % uid, data=json.dumps(song),
                content_type='application/json')

            song_id = json.loads(resp.data)['itemId']

            song['saved'] = 1

            resp = self.client.put(
                'user/%s/queue/%s' % (uid, song_id),
                data=json.dumps(song),
                content_type='application/json')

        expect(db.session.query(QueueItem).get(song_id).listened)


class TestUpdateUser(TestView):

    def it_returns_403_when_updating_a_different_user(self):
        user1, uid1 = self.login(satshabad)
        song = make_song_from(user1)

        self.logout()

        user2, uid2 = self.login(fateh)

        user1['lastFMUsername'] = 'satshabad'

        resp = self.client.put(
            'user/%s' % uid1,
            data=json.dumps(song),
            content_type='application/json')

        expect(resp.status_code) == 403

    def it_adds_the_last_fm_name_to_the_user(self):
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        user['lastFMUsername'] = 'ssk'

        resp = self.client.put(
            'user/%s' % uid,
            data=json.dumps(user),
            content_type='application/json')

        expect(resp.status_code) == 200
        expect(db.session.query(User).one().lastfm_name) == "ssk"

    def it_adds_the_twitter_name_to_the_user(self):
        user, uid = self.login(satshabad)
        song = make_song_from(user)

        user['twitterUsername'] = 'satshabad'

        resp = self.client.put(
            'user/%s' % uid,
            data=json.dumps(user),
            content_type='application/json')

        expect(resp.status_code) == 200
        expect(db.session.query(User).one().twitter_name) == "satshabad"

class TestPush(TestView):

    @patch('api.lib.push.APNs')
    def it_has_the_cert(self, apns):
        api.lib.push.push(
            "e9d331ab1c676b1ddc559ef0ead0dfed8c97bd682facb9c5ee818ba3ae51577e",
            "message",
            2,
            "satshabad",
            "song")

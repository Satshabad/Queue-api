import calendar
import json

from api import db

ForeignKey = db.ForeignKey
ForeignKeyConstraint = db.ForeignKeyConstraint
relationship = db.relationship
backref = db.backref
Column = db.Column
Integer = db.Integer
String = db.String
Boolean = db.Boolean


class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    fb_id = Column(Integer)
    lastfm_name = Column(String)
    twitter_name = Column(String)
    fullname = Column(String)
    image_link = Column(String)
    access_token = Column(String)
    device_token = Column(String)
    badge_setting = Column(String)
    badge_num = Column(Integer)
    claimed = Column(Boolean)

    def is_authenticated(self):
       return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def dictify(self):
        return {'userID':self.id,
                'fbId':self.fb_id,
                'fullName':self.fullname,
                'badgeSetting':self.badge_setting,
                "badge":self.badge_num,
                'image':self.image_link,
                'lastFMUsername':self.lastfm_name,
                'accessToken':self.access_token,
                'deviceToken':self.device_token,
                'imageLink':self.image_link}

    def limted_dictify(self):
        return {'userID':self.id,
                'fbId':self.fb_id,
                'fullName':self.fullname,
                'image':self.image_link,
                'imageLink':self.image_link}

    def __repr__(self):
        return "<User('%s','%s', '%s')>" % (self.id, self.fullname, self.image_link)

class Friend(db.Model):
    __tablename__ = 'friends'

    id = Column(Integer, primary_key=True)
    fullname = Column(String)
    fb_id = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", backref=backref('friends', order_by=fullname))

    def dictify(self):
        return {'name':self.fullname,
                 'fbId':self.fb_id }


    def __repr__(self):
        return "<Friend('%s', '%s')", (self.fullname, self.user)

class QueueItem(db.Model):
    __tablename__ = 'queue_items'

    id = Column(Integer, primary_key=True)
    date_queued = Column(Integer)
    no_show = Column(Boolean)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", foreign_keys=[user_id],
                        backref=backref('queue_items', order_by=date_queued))

    queued_by_id = Column(Integer, ForeignKey('users.id'))
    queued_by_user = relationship("User", foreign_keys=[queued_by_id],
                                  backref=backref('sent_queue_items', order_by=date_queued))

    urls_id = Column(Integer, ForeignKey('urlsforitems.id'))
    urls = relationship("UrlsForItem", foreign_keys=[urls_id], backref=backref('queue_item', order_by=id))

    listened = Column(Boolean)

    def get_item(self):
        found = False
        item = None
        item_type = None

        if self.song_item:
            if found:
                raise Exception("QueueItem has more than 1 media")
            found = True
            item = self.song_item[0]
            item_type = 'song'

        if self.note_item:
            if found:
                raise Exception("QueueItem has more than 1 media")
            found = True
            item = self.note_item[0]
            item_type = 'note'

        if self.artist_item:
            if found:
                raise Exception("QueueItem has more than 1 media")
            found = True
            item = self.artist_item[0]
            item_type = 'artist'

        if self.album_item:
            if found:
                raise Exception("QueueItem has more than 1 media")
            found = True
            item = self.album_item[0]
            item_type = 'album'

        return item_type, item

    def dictify(self):
        item_type, item = self.get_item()
        from_user =  self.queued_by_user.dictify()
        del from_user['accessToken']
        return {'itemId':self.id,
                'saved': 1 if self.listened else 0,
                'fromUser': from_user,
                'toUser': self.user.limted_dictify(),
                'urls':self.urls.dictify(),
                'type': item_type,
                item_type: item.dictify(),
                'dateQueued':self.date_queued
        }

    def __repr__(self):
        return "<QueueItem('%s', '%s', '%s', '%s')" % (self.id, self.user, self.queued_by_user, self.listened)


class SongItem(db.Model):
    __tablename__ = 'song_items'

    id = Column(Integer, ForeignKey('queue_items.id'), primary_key=True)
    queue_item = relationship("QueueItem",  foreign_keys=[id], backref=backref('song_item'))

    artist_id = Column(Integer, ForeignKey('artists.id'))
    artist = relationship("Artist", backref=backref('songs', order_by=id))

    album_id = Column(Integer, ForeignKey('albums.id'))
    album = relationship("Album", backref=backref('songs', order_by=id))

    name = Column(String)

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)
    extra_large_image_link = Column(String)

    def dictify(self):
        return {
                'artist': self.artist.dictify(),
                'album': self.album.dictify(),
                'name': self.name,
                'images':{
                    'small':self.small_image_link,
                    'medium':self.medium_image_link,
                    'large':self.large_image_link,
                    'extraLarge':self.extra_large_image_link
                 }
        }


    def __repr__(self):
        return "<Song('%s','%s', '%s', '%s')>" % (self.id, self.name, self.artist, self.album)

class NoteItem(db.Model):
    __tablename__ = 'note_items'

    id = Column(Integer, ForeignKey('queue_items.id'), primary_key=True)
    queue_item = relationship("QueueItem",  foreign_keys=[id], backref=backref('note_item'))

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)
    extra_large_image_link = Column(String)
    text = Column(String)

    def dictify(self):
        return {
                'text':self.text,
                'images':{
                    'small':self.small_image_link,
                    'medium':self.medium_image_link,
                    'large':self.large_image_link,
                    'extraLarge':self.extra_large_image_link
                 }
        }


    def __repr__(self):
        return "<NoteItem('%s','%s')>" % (self.id, self.text)

class ArtistItem(db.Model):
    __tablename__ = 'artist_items'

    id = Column(Integer, ForeignKey('queue_items.id'), primary_key=True)
    queue_item = relationship("QueueItem",  foreign_keys=[id], backref=backref('artist_item'))

    name = Column(String)

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)
    extra_large_image_link = Column(String)

    def dictify(self):
        return {
                'name':self.name,
                'images':{
                    'small':self.small_image_link,
                    'medium':self.medium_image_link,
                    'large':self.large_image_link,
                    'extraLarge':self.extra_large_image_link
                }
        }


    def __repr__(self):
        return "<ArtistItem('%s','%s')>" % (self.id, self.name)

class AlbumItem(db.Model):
    __tablename__ = 'album_items'

    id = Column(Integer, ForeignKey('queue_items.id'), primary_key=True)

    queue_item = relationship("QueueItem",  foreign_keys=[id], backref=backref('album_item'))


    name = Column(String)

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)
    extra_large_image_link = Column(String)

    def dictify(self):
        return {
                'name':self.name,
                'images':{
                    'small':self.small_image_link,
                    'medium':self.medium_image_link,
                    'large':self.large_image_link,
                    'extraLarge':self.extra_large_image_link
                }
        }


    def __repr__(self):
        return "<AlbumItem('%s','%s', '%s')>" % (self.id, self.name)



class Artist(db.Model):
    __tablename__ = 'artists'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)
    extra_large_image_link = Column(String)

    def dictify(self):
        return {
                'name':self.name,
                'images':{
                        'small':self.small_image_link,
                        'medium':self.medium_image_link,
                        'large':self.large_image_link,
                        'extraLarge':self.extra_large_image_link
                    }}


    def __repr__(self):
        return "<Artist('%s','%s')>" % (self.name, self.id)


class Album(db.Model):
    __tablename__ = 'albums'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    mbid = Column(String)

    def dictify(self):
        return {
                'name':self.name,
                }


    def __repr__(self):
        return "<Album('%s','%s')>" % (self.name, self.id)

class UrlsForItem(db.Model):
    __tablename__ = "urlsforitems"
    id = Column(Integer, primary_key=True)
    spotify_url = Column(String)
    grooveshark_url = Column(String)
    youtube_url = Column(String)
    other_url = Column(String)


    def dictify(self):
        return {
                'spotify':self.spotify_url,
                'grooveshark':self.grooveshark_url,
                'youtube':self.youtube_url,
                'other':self.other_url
                }


    def __repr__(self):
        return "<Urls('%s','%s')>" % (self.spotify_url, self.id)





import calendar
import json

from main import db

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
    uname = Column(String)
    fullname = Column(String)
    image_link = Column(String)
    access_token = Column(String)

    def dictify(self):
        return {'userName':self.uname,
                'fullName':self.fullname,
                'image':self.image_link}

    def __repr__(self):
        return "<User('%s','%s', '%s')>" % (self.uname, self.fullname, self.image_link)

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

        if self.song_item:
            if found:
                raise Exception("QueueItem has more than 1 media")
            found = True
            item = song_item[0]

        if self.note_item:
            if found:
                raise Exception("QueueItem has more than 1 media")
            found = True
            item = self.note_item[0]

        if self.artist_item:
            if found:
                raise Exception("QueueItem has more than 1 media")
            found = True
            item = self.artist_item[0]

        if self.album_item:
            if found:
                raise Exception("QueueItem has more than 1 media")
            found = True
            item = self.album_item[0]

        return item

    def dictify(self):
        return {'itemId':self.id,
                'listened': 1 if self.listened else 0,
                'fromUser': self.queued_by_user.dictify(),
                'urls':self.urls.dictify(),
                'item':self.get_item().dictify(),
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

    def dictify(self):
        return {'type': 'song',
                'song':{
                    'artist': self.artist.dictify(),
                    'album': self.album.dictify(),
                    'name': self.name,
                    'images':{
                        'small':self.small_image_link,
                        'medium':self.medium_image_link,
                        'large':self.large_image_link
                     }
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

    text = Column(String)

    def dictify(self):
        return {'type':'note',
                'note':{
                    'text':self.text,
                    'images':{
                        'small':self.small_image_link,
                        'medium':self.medium_image_link,
                        'large':self.large_image_link
                     }
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

    def dictify(self):
        return {'type':'artist',
                'artist':{
                    'name':self.name,
                    'images':{
                        'small':self.small_image_link,
                        'medium':self.medium_image_link,
                        'large':self.large_image_link
                    }
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

    def dictify(self):
        return {'type':'album',
                'album':{
                    'name':self.name,
                    'images':{
                        'small':self.small_image_link,
                        'medium':self.medium_image_link,
                        'large':self.large_image_link
                    }
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

    def dictify(self):
        return {
                'name':self.name,
                'images':{
                        'small':self.small_image_link,
                        'medium':self.medium_image_link,
                        'large':self.large_image_link
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

    def dictify(self):
        return {
                'spotify':self.spotify_url,
                }


    def __repr__(self):
        return "<Urls('%s','%s')>" % (self.spotify_url, self.id)





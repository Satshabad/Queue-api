import calendar
import json

from queue import db

ForeignKey = db.ForeignKey
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

class SongItem(db.Model):
    __tablename__ = 'song_items'

    id = Column(Integer, primary_key=True)
    listened = Column(Boolean)
    spotifylink = Column(String)
    date_queued = Column(Integer)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", foreign_keys=[user_id], backref=backref('song_items', order_by=date_queued))

    queued_by_id = Column(Integer, ForeignKey('users.id'))
    queued_by_user = relationship("User", foreign_keys=[queued_by_id], backref=backref('sent_song_items', order_by=date_queued))

    artist_id = Column(Integer, ForeignKey('artists.id'))
    artist = relationship("Artist", backref=backref('songs', order_by=id))

    album_id = Column(Integer, ForeignKey('albums.id'))
    album = relationship("Album", backref=backref('songs', order_by=id))

    urls_id = Column(Integer, ForeignKey('urlsforitems.id'))
    urls = relationship("UrlsForItem", foreign_keys=[urls_id], backref=backref('song_item', order_by=date_queued))

    name = Column(String)

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)

    def dictify(self):
        return {'itemId':self.id,
                'type': 'song',
                'listened': 1 if self.listened else 0,
                'fromUser': self.queued_by_user.dictify(),
                'urls':self.urls.dictify(),
                'song':{
                    'artist': self.artist.dictify(),
                    'album': self.album.dictify(),
                    'name': self.name,
                    'images':{
                        'small':self.small_image_link,
                        'medium':self.medium_image_link,
                        'large':self.large_image_link
                     }
                },
                'dateQueued':self.date_queued
              }


    def __repr__(self):
        return "<Song('%s','%s', '%s', '%s')>" % (self.name, self.artist, self.album, self.user_id)

class NoteItem(db.Model):
    __tablename__ = 'note_items'

    id = Column(Integer, primary_key=True)
    listened = Column(Boolean)
    spotifylink = Column(String)
    date_queued = Column(Integer)

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)


    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", foreign_keys=[user_id], backref=backref('note_items', order_by=date_queued))

    queued_by_id = Column(Integer, ForeignKey('users.id'))
    queued_by_user = relationship("User", foreign_keys=[queued_by_id], backref=backref('sent_note_items', order_by=date_queued))

    urls_id = Column(Integer, ForeignKey('urlsforitems.id'))
    urls = relationship("UrlsForItem", foreign_keys=[urls_id], backref=backref('note_item', order_by=date_queued))


    text = Column(String)

    def dictify(self):
        return {'itemId':self.id,
                'type':'note',
                'note':{
                    'text':self.text,
                    'images':{
                        'small':self.small_image_link,
                        'medium':self.medium_image_link,
                        'large':self.large_image_link
                     }
                },
                'urls':self.urls.dictify(),
                'listened': 1 if self.listened else 0,
                'fromUser': self.queued_by_user.dictify(),
                'dateQueued':self.date_queued
        }


    def __repr__(self):
        return "<NoteItem('%s','%s', '%s')>" % (self.name, self.id, self.user)

class ArtistItem(db.Model):
    __tablename__ = 'artist_items'

    id = Column(Integer, primary_key=True)
    listened = Column(Boolean)
    spotifylink = Column(String)
    date_queued = Column(Integer)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", foreign_keys=[user_id], backref=backref('artist_items', order_by=date_queued))

    queued_by_id = Column(Integer, ForeignKey('users.id'))
    queued_by_user = relationship("User", foreign_keys=[queued_by_id], backref=backref('sent_artist_items', order_by=date_queued))

    urls_id = Column(Integer, ForeignKey('urlsforitems.id'))
    urls = relationship("UrlsForItem", foreign_keys=[urls_id], backref=backref('artist_item', order_by=date_queued))

    name = Column(String)

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)

    def dictify(self):
        return {'itemId':self.id,
                'type':'artist',
                'listened': 1 if self.listened else 0,
                'fromUser': self.queued_by_user.dictify(),
                'dateQueued':self.date_queued,
                'urls':self.urls.dictify(),
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
        return "<ArtistItem('%s','%s', '%s')>" % (self.name, self.id, self.user)

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





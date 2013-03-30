import calendar
import json

from queue import db

ForeignKey = db.ForeignKey
relationship = db.relationship
backref = db.backref
Column = db.Column
Integer = db.Integer
String = db.String
DateTime = db.DateTime
Boolean = db.Boolean



class User(db.Model):
    __tablename__ = 'users'

    def __init__(self, name, auth):
        self.uname = name
        self.auth = auth

    id = Column(Integer, primary_key=True)
    fb_id = Column(Integer)
    uname = Column(String)
    fullname = Column(String)
    image_link = Column(String)
    auth = Column(String)

    def dictify(self):
        return {'user_name':self.uname,
                'full_name':self.fullname,
                'image':self.image_link}

    def __repr__(self):
        return "<User('%s','%s', '%s')>" % (self.uname, self.fullname, self.image_link)

class Friend(db.Model):
    __tablename__ = 'friends'

    def __init__(self, name, fb_id, user):
        self.fullname = name
        self.fb_id = fb_id
        self.user = user

    id = Column(Integer, primary_key=True)
    fullname = Column(String)
    fb_id = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", backref=backref('friends', order_by=fullname))

    def dictify(self):
        return {'name':self.fullname,
                'fb_id':self.fb_id }


    def __repr__(self):
        return "<Friend('%s', '%s')", (self.fullname, self.user)

class SongItem(db.Model):
    __tablename__ = 'song_items'

    id = Column(Integer, primary_key=True)
    listened = Column(Boolean)
    spotifylink = Column(String)
    date_queued = Column(DateTime)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", foreign_keys=[user_id], backref=backref('song_items', order_by=date_queued))

    queued_by_id = Column(Integer, ForeignKey('users.id'))
    queued_by_user = relationship("User", foreign_keys=[queued_by_id], backref=backref('sent_song_items', order_by=date_queued))

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
                'listened': 1 if self.listened else 0,
                'from_user': self.queued_by_user.dictify(),
                'artist': self.artist.dictify(),
                'album': self.album.dictify(),
                'name': self.name,
                'date_queued':calendar.timegm(self.date_queued.utctimetuple()),
                'images':{
                        'small':self.small_image_link,
                        'medium':self.medium_image_link,
                        'large':self.large_image_link
                  }}


    def __repr__(self):
        return "<Song('%s','%s', '%s', '%s')>" % (self.name, self.artist, self.album, self.user_id)

class NoteItem(db.Model):
    __tablename__ = 'note_items'

    id = Column(Integer, primary_key=True)
    listened = Column(Boolean)
    spotifylink = Column(String)
    date_queued = Column(DateTime)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", foreign_keys=[user_id], backref=backref('note_items', order_by=date_queued))

    queued_by_id = Column(Integer, ForeignKey('users.id'))
    queued_by_user = relationship("User", foreign_keys=[queued_by_id], backref=backref('sent_note_items', order_by=date_queued))

    text = Column(String)

    def dictify(self):
        return {'type':'note',
                'listened': 1 if self.listened else 0,
                'from_user': self.queued_by_user.dictify(),
                'date_queued':calendar.timegm(self.date_queued.utctimetuple()),
                'text':self.text
                }


    def __repr__(self):
        return "<NoteItem('%s','%s', '%s')>" % (self.name, self.id, self.user)

class ArtistItem(db.Model):
    __tablename__ = 'artist_items'

    id = Column(Integer, primary_key=True)
    listened = Column(Boolean)
    spotifylink = Column(String)
    date_queued = Column(DateTime)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", foreign_keys=[user_id], backref=backref('artist_items', order_by=date_queued))

    queued_by_id = Column(Integer, ForeignKey('users.id'))
    queued_by_user = relationship("User", foreign_keys=[queued_by_id], backref=backref('sent_artist_items', order_by=date_queued))

    name = Column(String)
    mbid = Column(String)

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)

    def dictify(self):
        return {
                'type':'artist',
                'listened': 1 if self.listened else 0,
                'from_user': self.queued_by_user.dictify(),
                'date_queued':calendar.timegm(self.date_queued.utctimetuple()),
                'name':self.name,
                'mbid':self.mbid,
                'images':{
                        'small':self.small_image_link,
                        'medium':self.medium_image_link,
                        'large':self.large_image_link
                    }}


    def __repr__(self):
        return "<ArtistItem('%s','%s', '%s')>" % (self.name, self.id, self.user)

class Artist(db.Model):
    __tablename__ = 'artists'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    mbid = Column(String)

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)

    def dictify(self):
        return {
                'name':self.name,
                'mbid':self.mbid,
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
                'mbid':self.mbid
                }


    def __repr__(self):
        return "<Album('%s','%s')>" % (self.name, self.id)


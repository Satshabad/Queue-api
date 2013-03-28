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

class Song(db.Model):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True)
    listened = Column(Boolean)
    spotifylink = Column(String)
    date_queued = Column(DateTime)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", foreign_keys=[user_id], backref=backref('queue', order_by=date_queued))

    queued_by_id = Column(Integer, ForeignKey('users.id'))
    queued_by_user = relationship("User", foreign_keys=[queued_by_id], backref=backref('sent', order_by=date_queued))

    artist_id = Column(Integer, ForeignKey('artists.id'))
    artist = relationship("Artist", backref=backref('songs', order_by=id))

    album_id = Column(Integer, ForeignKey('albums.id'))
    album = relationship("Album", backref=backref('songs', order_by=id))

    name = Column(String)

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)

    def dictify(self):
        return {'listened': 1 if self.listened else 0,
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


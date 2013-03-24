import sqlalchemy
from sqlalchemy import Column, Integer, String
from sqlalchemy.types import DateTime, Boolean

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    uname = Column(String)
    fullname = Column(String)
    image_link = Column(String)

    def __repr__(self):
        return "<User('%s','%s', '%s')>" % (self.uname, self.fullname, self.image_link)

class Song(Base):
    __tablename__ = 'songs'

    id = Column(String, primary_key=True)
    rank = Column(Integer)

    user_id = Column(Integer, ForeignKey('users.id')
    user = relationship("User", backref=backref('songs', order_by=rank))

    artist_id = Column(Integer, ForeignKey('artists.id'))
    artist = relationship("Artist", backref=backref('songs', order_by=id))

    album_id = Column(Integer, ForeignKey('albums.id'))
    album = relationship("Albums", backref=backref('songs', order_by=id))

    name = Column(String)
    date = Column(DateTime)

    small_image_link = Column(String)
    medium_image_link = Column(String)
    large_image_link = Column(String)

    def __repr__(self):
        return "<Song('%s', '%s','%s', '%s')>" % (self.rank, self.name, self.artist, self.album)

class Artist(Base):
    __tablename__ = 'artists'

    id = Column(String, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return "<Artist('%s','%s')>" % (self.name, self.id)


class Album(Base):
    __tablename__ = 'album'

    id = Column(String, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return "<Artist('%s','%s')>" % (self.name, self.id)

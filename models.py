from peewee import *
from dungeon import db
import datetime

class Player:
    """
    In-memory representation of a player
    """

    def __init__(self, connection):
        self.appearance = "male" # name of the sprite to use for representing a player
        self.position = (0, 0) # positions don't need to be stored in sql
        self.connection = connection
        self.stream = connection.stream
        self.floor = -1
        self.steam_id = None
        self.name = "An Unknown Soul"
        self.dead = False 
        self.dead_to = None

        # this should be flagged as True once the "connected" message is received from
        # the client.  A connection should not have any messages cast to it until the
        # player has been marked as loaded
        self.loaded = False

    @property
    def id(self):
        """
        Players should be primarily identified by their steam_id,
        else their connection id, so as to prevent a flood of corpses
        on any floor
        """
        if self.steam_id is not None:
            return self.steam_id
        return self.connection.id


class DeadPlayer(Model):
    steam_id = PrimaryKeyField()
    steam_name = CharField(default="Adventurer")
    dead_to = CharField()
    level = IntegerField()
    x = IntegerField()
    y = IntegerField()

    class Meta:
        database = db

    def __iter__(self):
        yield ('id', self.steam_id)
        yield ('name', self.steam_name)
        yield ('dead_to', self.dead_to)
        yield ('x', self.x)
        yield ('y', self.y)

def _expiration():
    return datetime.datetime.now() + datetime.timedelta(days=2)

class UserDungeon(Model):
    """
    DB representation of a user uploaded "file"
    """
    seed = BigIntegerField()
    filename = CharField()
    extension = CharField()
    filesize = IntegerField()
    uploader = CharField(default="Adventurer")
    expiration_date = DateTimeField(default=_expiration)

    class Meta:
        database = db

    def __iter__(self):
        yield ('seed', self.seed)
        yield ('filename', self.filename)
        yield ('extension', self.extension)
        yield ('filesize', self.filesize)
        yield ('uploader', self.uploader)
        yield ('expiration', self.expiration_date.timestamp())
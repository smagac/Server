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
        self.steam_id = -1
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
        if self.steam_id > 0:
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

def _expiration():
    return datetime.datetime.now() + datetime.timedelta(days=2)

class UserDungeon(Model):
    """
    DB representation of a user uploaded "file"
    """
    seed = BigIntegerField()
    filename = CharField()
    difficulty = IntegerField()
    filesize = IntegerField()
    uploader = CharField(default="Adventurer")
    expiration_date = DateTimeField(default=_expiration)
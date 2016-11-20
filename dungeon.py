import sqlite3, atexit, random
import schedule
from peewee import *
from datetime import datetime
from contextlib import closing

# configuration
DATABASE = './sm_daily.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# Dungeon specifications
_TYPES = ["Other", "Audio", "Image", "Compressed", "Video", "Executable"]
_SEEDSIZE = 63

_dungeon = {
    'seed':0,
    'difficulty':0,
    'type':None
}

db = SqliteDatabase(DATABASE)

def create_dungeon():
    seed = random.getrandbits(_SEEDSIZE)
    filetype = random.choice(_TYPES)
    difficulty = random.randint(1, 5)
    _dungeon['seed'] = seed
    _dungeon['type'] = filetype
    _dungeon['difficulty'] = difficulty
    

def create_tables():
    import models
    db.connect()
    try:
        db.create_tables([models.DeadPlayer])
    # ignore if the tables exist already
    except OperationalError:
        pass

# create a new dungeon every day at midnight
schedule.every().day.at("00:00").do(create_dungeon)

def main():
    from server import StorymodeTCPServer
    import tornado.ioloop

    # make sure db exists
    create_tables()

    # configuration
    host = '0.0.0.0'
    port = 8008

    # tcp server
    server = StorymodeTCPServer()
    server.listen(port, host)
    print("Listening on %s:%d..." % (host, port))

    # infinite loop
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
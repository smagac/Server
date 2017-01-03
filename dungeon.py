import sqlite3, atexit, random
import schedule
from peewee import *
from datetime import datetime
from contextlib import closing

# configuration
DATABASE = 'sm_daily.db'
DEBUG = True

# Dungeon specifications
_TYPES = ["Other", "Audio", "Image", "Compressed", "Video", "Executable"]
_SEEDSIZE = 63

class Dungeon:
    def __init__(self):
        self.refresh()

    def refresh(self):
        self.seed = random.getrandbits(_SEEDSIZE)
        self.difficulty = random.randint(1, 5)
        self.filetype = random.choice(_TYPES)

    def __iter__(self):
        yield ('seed', self.seed)
        yield ('type', self.filetype)
        yield ('difficulty', self.difficulty)

db = SqliteDatabase(DATABASE, autocommit=True)

def create_tables():
    import models
    db.connect()
    db.create_tables([models.DeadPlayer, models.UserDungeon], True)
    

def main():
    import server
    import web
    import tornado.ioloop
    import tornado.web

    # make sure db exists
    create_tables()

    # make sure dungeon exists
    dungeon = Dungeon()

    # create a new dungeon every day at midnight
    schedule.every().day.at("00:00").do(dungeon.refresh)

    # configuration
    host = '0.0.0.0'
    tcpport = 8081
    httpport = 8080

    # tcp server
    server = server.StorymodeTCPServer()
    server.listen(tcpport, host)
    print("Listening on %s:%d..." % (host, tcpport))

    # http server
    http = tornado.web.Application([
        (r'/daily', web.DailyDungeonRequestHandler, dict(dungeon=dungeon)),
        (r'/community', web.UserUploadRequestHandler, dict(db=db)),
    ])
    http.listen(httpport, host)
    print("Listening on %s:%d..." % (host, httpport))


    # infinite loop
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
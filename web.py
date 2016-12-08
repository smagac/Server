"""
Simple application used for handling standard web requests
This is used for distributing the daily dungeon while maintaining
backwards compatibility with older clients.

It is also used as the location for managing user uploaded dungeons
"""
import tornado.web
import tornado.escape
import models
import json

class DailyDungeonRequestHandler(tornado.web.RequestHandler):
    def initialize(self, dungeon):
        self.dungeon = dungeon

    def get(self):
        """
        @return the current daily dungeon JSON spec
        """
        self.write(
            json.dumps(dict(self.dungeon))
        )

class UserUploadRequestHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    def post(self):
        """
        Handle creating a new user dungeon
        """
        data = tornado.escape.json_decode(self.request.body)
            
        with self.db.transaction():
            dungeon = models.UserDungeon.create(
                seed=data['seed'],
                filename=data['filename'],
                difficulty=data['difficulty'],
                filesize=data['filesize'],
                uploader=data['uploader']
            )
        
        # write back created dungeon
        self.write(
            json.dumps(dungeon)
        )

    def get(self):
        """
        Get a list of user uploaded dungeons
        """
        self.write(
            json.dumps([
                dungeon for dungeon in models.UserDungeon.select()
            ])
        )
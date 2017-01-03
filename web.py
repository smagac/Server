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
import traceback, sys
from http import HTTPStatus

from playhouse.shortcuts import model_to_dict

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
        self.set_status(HTTPStatus.OK)
        self.finish()

class UserUploadRequestHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    def post(self):
        """
        Handle creating a new user dungeon
        """
        print(self.request.body)
        data = tornado.escape.json_decode(self.request.body)
        
        try:        
            self.db.connect()
            with self.db.transaction():
                dungeon = models.UserDungeon.create(
                    seed=data['seed'],
                    filename=data['filename'],
                    extension=data['extension'],
                    filesize=data['filesize'],
                    uploader=data['uploader'] or models.UserDungeon.uploader.default
                )
            # write back created dungeon
            self.write(
                json.dumps(dict(dungeon))
            )
            self.set_status(HTTPStatus.CREATED)
        except Exception as e:
            self.set_status(HTTPStatus.NOT_ACCEPTABLE)
            traceback.print_exc(file=sys.stdout)
        finally:
            self.db.close()
            self.finish()
        

    def get(self):
        """
        Get a list of user uploaded dungeons
        """
        self.write(
            json.dumps([
                dict(dungeon) for dungeon in models.UserDungeon.select()
            ])
        )
        self.finish()

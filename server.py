
import tornado.tcpserver

from connection import Connection
from messages import EventHandler

class StorymodeTCPServer(tornado.tcpserver.TCPServer):
    """
    TCPServer and in-memory world representation of the current daily
    dungeon floor
    """
    def __init__(self):
        super().__init__()
        self.connections = []

        # handles location of the players so we only need
        # to distribute messages to floors instead of everyone
        self.floors = {}
        self.event_handler = EventHandler(self)

    @tornado.gen.coroutine
    def handle_stream(self, stream, address):
        """
        Called for each new connection, stream.socket is
        a reference to socket object
        """
        connection = Connection(self, stream)
        yield connection.on_connect()

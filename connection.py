import socket

import tornado.gen
import tornado.ioloop
import tornado.iostream
import tornado.tcpserver

import models
import json
import traceback

class Connection:
    """
    Representation of a player's connection to the daily dungeon server
    This connection will receive messages, which are parsed by the event
    handler, and will also maintain an in-memory representation of the player
    on the server.
    """
    client_id = 0

    def __init__(self, server, stream):
        super().__init__()
        # increment the unique id of the connection
        Connection.client_id += 1
        
        self.id = Connection.client_id
        self.stream = stream
        self.server = server

        # initialize the socket type
        self.stream.socket.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.stream.socket.setsockopt(
            socket.IPPROTO_TCP, socket.SO_KEEPALIVE, 1)

        # add a callback for disconnection
        self.stream.set_close_callback(self.on_disconnect)
        self.player = models.Player(self)
        self.peer = 'closed'

    @tornado.gen.coroutine
    def on_disconnect(self):
        """
        Executed function when the socket closes.
        """

        # for now we currently have no functionality planned for disconnection
        self.server.connections.remove(self)

    @tornado.gen.coroutine
    def dispatch_client(self):
        """
        Loop that handles receiving messages from the socket
        """
        try:
            while True:
                # messages are read in by line
                line = yield self.stream.read_until(b'\n') 
                line = line.decode('utf-8') # convert bytes into string

                # read the json from the message
                try:
                    print(line)
                    payload = json.loads(line)
                    # for debugging purposes, track what responses we're receiving
                    self.log(str(payload))

                    # handle the event type associated with the message
                    yield self.server.event_handler.handle_message(self.player, payload)
                except Exception as e:
                    traceback.print_exc()
                    self.log("message must be json")
        except tornado.iostream.StreamClosedError:
            # handle closed processing within on_disconnect instead of here
            pass

    @tornado.gen.coroutine
    def on_connect(self):
        """
        Performs on connection processing
        """

        # add this connection into the server to keep track of
        self.server.connections.append(self)

        # identify the connection's address (used for debugging purposes)
        self.peer = 'closed'
        try:
            self.peer = '%s:%d' % self.stream.socket.getpeername()
        except Exception:
            pass

        # yeild the process to start handling client messages
        yield self.dispatch_client()

    def log(self, msg):
        print('[connection {}] {}'.format(self.peer, msg))


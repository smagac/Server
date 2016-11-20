import models
from dungeon import db

class EventHandler:
    """
    Event handler used by the storymode server
    When a json payload is received over a socket, it identifies
    what kind of event type it is associated with.  The event handler
    will then invoke the message associated with that event type.

    Handler methods are defined using the naming scheme of
        on_[event_name]
    """
    def __init__(self, server):
        self.server = server

    def _send_message(self, floor, message, exclude=[]):
        """
        Allow sending a batch message to all players on a floor
        """
        for player in self.server.floors.get(floor, dict()).values():
            if player not in exclude:
                player.stream.write(json.dumps(message))

    def handle_message(self, player: models.Player, payload: dict):
        """
        Invokes a method on this event handler based on the payload type
        """
        if payload.get("type"):
            handler = getattr(self, 'on_'+payload['type'], None)
            if handler:
                print(handler)
                if player.loaded or (handler == self.on_connect and not player.loaded):
                    return handler(player, payload) or {}
        return {}

    def on_connect(self, player: models.Player, payload: dict):
        """
        Initial connection information, providing the server
        with the identifying credentials of the player.
        """
        print("connecting player data")
        player.appearance = payload['appearance']
        player.steam_id = properties['steam_id']
        player.steam_name = properties['steam_name']
        player.loaded = True

        return {}


    def on_floor(self, player: models.Player, payload: dict):
        """
        Sets the floor that the player is currently positioned on
        """
        floor = payload['floor']

        # if player is already located on a floor, tell everyone
        # else on that floor that the player is leaving
        if player.floor != -1:
            self._send_message(player.floor, {
                'type': 'remove',
                'player': p.uid,
            }, [player])
            floors.get(player.floor, list()).remove(player)

        player.floor = payload['floor']
        player.position = payload['position']

        # add the player to the new floor
        players = floors.get(player.floor, list())
        players.append(player)
        floors.put(player.floor, players)

        # inform player of the dead on this floor as well as other connected players
        dead = []
        with db.transaction():
            dead = models.DeadPlayer.select().where(
                Person.level == player.floor,
            )

        return player.stream.write(json.dumps({
            'dead': [
                {
                    'steam_id': p.steam_id,
                    'steam_name': p.steam_name,
                    'dead_to': p.dead_to,
                    'x': p.x,
                    'y': p.y, 
                } for p in dead if p.steam_id != player.id
            ],
            'players': [
                {
                    'id': p.id,
                    'position' : p.position,
                    'appearance': p.appearance,
                } for p in players if p != player
            ]
        }))


    def on_dead(self, player: models.Player, payload: dict):
        """
        Handles informing other players of when and where
        and player dies on the floor
        """
        user = self.connected_users.get(origin)
        died_to = payload['dead_to']
        
        # save response into the sql db
        with db.transaction():
            models.DeadPlayer.create(
                steam_id = player.steam_id,
                steam_name = player.steam_name,
                x = player.position[0],
                y = player.position[1],
                level = player.floor,
                dead_to = died_to,
            ).execute()
        

        # send the message to everyone so they know who died
        self._send_message(player.floor, {
            "type": "dead",
            "player": user.uid,
            "died_to": died_to,
            "position": user.position
        }, exclude=[player])

        return {}

    def on_move(self, player: models.Player, payload: dict):
        """
        Handles moving the player to a new position on the floor
        and notifying all connected users on that floor of the
        player's new position
        """
        player.position = payload['position']
        self._send_message(player.floor, {
            'type': 'move',
            'id': player.uid,
            'position': player.position
        }, exclude=[player])

        return {}
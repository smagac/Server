import models
import json
from dungeon import db
from typing import List

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

    def _send_message(self, target = None, message: dict = {}, exclude: List[models.Player] = []):
        """
        Allow sending a batch message to all players on a floor
        """
        print(message)
        if target is not None and isinstance(target, int):
            for player in self.server.floors.get(target, list()):
                if player not in exclude:
                    player.stream.write(str.encode(json.dumps(message) + "\n"))
            return {}
        else:
            return target.stream.write(str.encode(json.dumps(message) + "\n"))

    def handle_message(self, player: models.Player, payload: dict):
        """
        Invokes a method on this event handler based on the payload type
        """
        if payload.get("type"):
            handler = getattr(self, 'on_'+payload['type'], None)
            if handler:
                if player.loaded or (handler == self.on_connect and not player.loaded):
                    return handler(player, payload) or {}
            else:
                print ("invalid type %s" % payload.get("type"))
        else:
            print ("invalid payload")
        return {}

    def on_connect(self, player: models.Player, payload: dict):
        """
        Initial connection information, providing the server
        with the identifying credentials of the player.  This
        message will not propagate data down to other players.
        To inform other players of your presence, you must
        set the floor you are are after connecting
        """
        print("connecting player data")
        player.appearance = payload['appearance']
        player.steam_id = payload['id']
        player.name = payload['name']
        player.loaded = True
        player.dead = False

        return None

    def on_disconnect(self, player: models.Player, payload: dict):
        if not player.dead:
            return self._send_message(
                target=player.floor, 
                message={
                    'type': 'disconnect', 
                    'id': player.id
                },
                exclude=[player]
            )
        return {}

    def on_floor(self, player: models.Player, payload: dict):
        """
        Sets the floor that the player is currently positioned on
        """
        floor = payload['floor']

        # if player is already located on a floor, tell everyone
        # else on that floor that the player is leaving
        if player.floor != -1:
            self._send_message(target=player.floor, message={
                'type': 'disconnect',
                'id': p.id,
            }, exclude=[player])
            self.server.floors.get(player.floor, list()).remove(player)

        player.floor = payload['floor']
        player.position = (payload['x'], payload['y'])

        # add the player to the new floor
        players = self.server.floors.get(player.floor, list())
        players.append(player)
        self.server.floors[player.floor] = players
        self._send_message(target=player.floor, message={
            'type': 'connect',
            'id': player.id,
            'name': player.name,
            'appearance': player.appearance,
            'x': player.position[0],
            'y': player.position[1]
        }, exclude=[player])

        # inform player of the dead on this floor as well as other connected players
        dead = []
        with db.transaction():
            dead = models.DeadPlayer.select().where(
                models.DeadPlayer.level == player.floor,
            )

        return self._send_message(target=player, message={
            'type': 'floor',
            'dead': [
                dict(p) for p in dead
            ],
            'players': [
                {
                    'id': p.id,
                    'name': p.name,
                    'x' : p.position[0],
                    'y' : p.position[1],
                    'appearance': p.appearance,
                } for p in players if p != player
            ]
        })


    def on_dead(self, player: models.Player, payload: dict):
        """
        Handles informing other players of when and where
        and player dies on the floor
        """
        player.dead = True
        
        # don't allow stacking
        with db.transaction():
            models.DeadPlayer.delete().where(
                models.DeadPlayer.x == player.position[0],
                models.DeadPlayer.y == player.position[1],
                models.DeadPlayer.level == player.floor
            ).execute()

        # move player's tombstone if they've already died today
        with db.transaction():
            deadPlayer, created = models.DeadPlayer.get_or_create(
                steam_id=player.id,
                defaults={
                    'x': player.position[0],
                    'y': player.position[1],
                    'level': player.floor,
                    'steam_id': player.id,
                    'steam_name': player.name,
                    'dead_to': payload['dead_to'],
                }
            )
            if not created:
                deadPlayer.dead_to = payload['dead_to']
                deadPlayer.x = player.position[0]
                deadPlayer.y = player.position[1]
                deadPlayer.level = player.floor
                deadPlayer.save()
             
        # send the message to everyone so they know who died
        return self._send_message(target=player.floor, message={
            'type': 'dead',
            **dict(deadPlayer)
        }, exclude=[player])

    def on_movement(self, player: models.Player, payload: dict):
        """
        Handles moving the player to a new position on the floor
        and notifying all connected users on that floor of the
        player's new position
        """
        player.position = (payload['x'], payload['y'])
        return self._send_message(target=player.floor, message={
            'type': 'movement',
            'id': player.id,
            'x' : player.position[0],
            'y' : player.position[1],
        }, exclude=[player])
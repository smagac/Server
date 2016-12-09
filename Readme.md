# API

Messages are to be sent as standard JSON.  The method to be invoked is indicated by the "type" field of the json message.

## Received Messages


Message Type | Parameters
-------------- | ------------
connect | appearance: string <br> id: int <br> name: string
move | x: int <br> y: int
floor | depth: int
dead | deadTo: string


## Sent Messages


Message Type | Parameters
--------------|------------
connect | appearance: string <br> id: int <br> name: string <br> x: int <br> y: int
move | id:int, x: int <br> y: int
floor | dead: Array[deadTo, x, y], players: Array[id, name, x, y]
disconnect | id: int
dead | id: int <br> deadTo: string
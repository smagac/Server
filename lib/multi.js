const _ = require('lodash');
const { Router } = require('express');

class Session {
    constructor(playerState, dungeon, redis, ws) {
        this.state = playerState;
        this.dungeon = dungeon;
        this.redis = redis;
        const messageHandler = (channel, message) => {
            const data = JSON.parse(message);
            // ignore self sent messages
            if (data.id && data.id === this.playerState.id) {
                return;
            }
            // ignore messages that may have come from other sessions on this same instance
            if (channel !== this.floorChannel() || channel !== this.privateChannel()) {
                return;
            }
            ws.send(message);
        };
        redis.subscribe(this.privateChannel());
        redis.on('message', messageHandler);
        ws.on('close', () => {
            this.redis.unsubscribe(this.privateChannel());
            this.redis.removeListener('message', messageHandler);
        });
    }

    update(playerState) {
        this.state = {
            ...this.state,
            ...playerState,
        };
        this.redis.hset(`multiplayer:${this.dungeon}`, this.state.id, this.state);
    }

    /**
     * Broadcast a message to other players
     * @param {object} msg 
     * @param {string} channel - redis channel to publish to, defaults to publishing to other players listening to this floor's messages
     */
    publish(msg, channel = this.floorChannel()) {
        this.redis.publish(
            channel,
            JSON.stringify(msg),
        );
    }

    /**
     * Subscription channel key for the user associated with this session
     */
    privateChannel() {
        return `private:${this.playerState.id}`;
    }

    /**
     * Public channel for the floor 
     * @param {*} floor 
     */
    floorChannel(floor = this.playerState.floor) {
        return `floor:${floor}`;
    }

    /**
     * Route ws messages to appropriate handler methods
     * @param {*} type 
     * @param {*} payload 
     */
    handleMessage(type, payload) {
        this[`on${_.capitalize(type)}`].apply(this, payload);
    }

    /**
     * Handle changing the floor that the player is currently on
     * Notifies other players of the presence of this one on each of the floors they're switching between
     * @param {object} payload
     * @param {number} payload.floor - new floor the player is one
     * @param {number} payload.x - x position in the grid the player will be on after switching floors
     * @param {number} payload.y - y position in the grid the player will be on after switching floors
     */
    async onFloor({
        floor,
        x,
        y
    }) {
        const previousFloor = this.state.floor;
        this.update(
            {
                floor,
                x,
                y,
            },
        );
        // change floor channels
        this.mConnection.multi()
            .unsubscribe(this.floorChannel(previousFloor))
            .subscribe(this.floorChannel(floor))
            .exec();
        const sessions = await this.mConnection.hvalues(`multiplayer:${this.dungeon}`);
        // broadcast to other users that you're changing floors
        this.publish(
            {
                type: 'disconnect',
                id: this.state.id
            },
            this.floorChannel(previousFloor),
        );
        this.publish(
            {
                type: 'disconnect',
                id: this.state.id,
                name: this.state.name,
                appearance: this.state.appearance,
                x: this.state.x,
                y: this.state.y
            },
            this.floorChannel(floor),
        );
        // inform user of who is on the floor
        this.publish(
            {
                type: 'floor',
                dead: _.sample(
                    sessions.filter(
                        pState => pState.floor === floor && !_.isNil(pState.deadTo),
                    ).map(
                        pState => ({
                            id: pState.id,
                            name: pState.name,
                            dead_to: pState.deadTo,
                            x: pState.deadX,
                            y: pState.deadY,
                        }), 
                    ), 
                    8
                ),
                players: _.sample(
                    sessions.filter(
                        pState => pState.id !== this.state.id && pState.dead === false,
                    ).map(
                        pState => ({
                            id: pState.id,
                            name: pState.name,
                            appearance: p.appearance,
                            x : pState.x,
                            y : pState.y,
                        }),
                    ),
                    32,
                ),
            },
            this.privateChannel(),
        );
    }

    /**
     * Handle moving a player and notifying other players of this player's position
     * @param {object} payload
     * @param {number} payload.x - x position in the map grid
     * @param {number} payload.y - y position in the map grid
     */
    onMovement({
        x,
        y,
    }) {
        this.update({
            x,
            y,
        });
        this.publish(
            {
                type: 'movement',
                id: this.state.id,
                x,
                y,
            }
        );
    }

    /**
     * Records the death of this player in the dungeon
     * @param {object} payload
     * @param {string} payload.dead_to Name of the enemy that killed this player
     */
    onDead({
        dead_to: deadTo,
    }) {
        this.update({
            deadTo,
            deadX: this.state.x,
            deadY: this.state.y,
        });
        this.publish(
            {
                type: 'dead',
                id: this.state.id,
                name: this.state.name,
                dead_to: this.state.deadTo,
                x: this.state.x,
                y: this.state.y,
            },
        );
    }
}

module.exports = (wss, dependencies) => {
    const { redis, logger } = dependencies;

    async function createSession({
        appearance,
        id,
        name,
    }) {
        logger.debug(`connecting player ${id}-${name}`);
        const seed = await redis.hget('daily_dungeon', 'seed');
        if (_.isNil(seed)) {
            logger.error('dungeon has not yet been initialized, can not connect user');
            return;
        }
        const state = await redis.hget(`multiplayer:${seed}`, id).then(JSON.parse);
        const session = new Session(
            {
                ...(state || { id }),
            }, 
            seed,
            // it's messy to reuse one connection for multiple sessions, but it helps for cost in heroku
            redis,
        );
        session.update(
            {
                appearance,
                id,
                name,
                floor: -1,
                x: -1,
                y: -1,
            }
        );
        return session;
    }

    const router = new Router();

    router.ws(
        '/',
        (ws) => {
            let session = null;
            ws.on('message', (msg) => {
                const payload = JSON.parse(msg);
                const {
                    type
                } = payload;
                if (type === 'connect') {
                    session = createSession(payload);
                } else if (session) {
                    session.handleMessage(type, payload);
                }
            });
        },
    );

    return router;
};

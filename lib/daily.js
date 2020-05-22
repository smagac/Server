const { validate, ValidationError, Joi } = require('express-validation')
const Router = require('express-promise-router');

const DUNGEON_TYPES = ["Other", "Audio", "Image", "Compressed", "Video", "Executable"];

module.exports = (dependencies) => {
    const { redis, logger } = dependencies;

    const router = new Router();

    router.get(
        '/daily',
        async (req, res) => {
            let [
                seed,
                type,
                difficulty,
            ] = await redis.hget(
                'daily_dungeon',
                'seed',
                'type',
                'difficulty',
            );

            // lazily create a new dungeon for the day
            if (seed === null) {
                logger.info('no daily dungeon found, reserving a new one.');
                seed = Math.random() * Number.MAX_VALUE;
                type = DUNGEON_TYPES[Math.random() * DUNGEON_TYPES.length];
                difficulty = Math.floor(Math.random() * 5) + 1;
            
                const now = new Date(),
                const expireAt = new Date(
                    now.getFullYear(),
                    now.getMonth(),
                    now.getDate(),
                    0,0,0
                ) + 86400000;  // daily dungeons only last until midnight, so reserve the multiplayer until then
                redis.set(`multiplayer:${seed}`, 1, 'EX', expireAt / 1000, 'NX');
                                
                redis.hset(
                    'daily_dungeon',
                    'seed', seed,
                    'type', type,
                    'difficulty', difficulty,
                );
                redis.expireAt('daily_dungeon', expireAt / 1000);
            }
            
            res.json({
                seed,
                type,
                difficulty,
            });
        }
    );

    router.get(
        '/community',
        async (req, res) => {
            const now = +Date.now();
            const files = await redis.smembers('uploads');
            const dungeons = files.filter(
                upload => upload.expiration > now,
            ).map(JSON.parse);

            res.json(dungeons);

            // lazily delete expired items
            redis.srem(
                'uploads',
                ...files.filter(upload => upload.expiration <= now),
            );
        },
    );

    router.post(
        '/community',
        validate({
            body: Joi.object({
                seed: Joi.number().required(),
                filename: Joi.string()
                    .required(),
                extension: Joi.string()
                    .required(),
                filesize: Joi.number()
                    .required(),
                uploader: Joi.string(),
            }),
        }),
        async (req, res) => {
            const {
                seed,
                filename,
                extension,
                filesize,
                uploader = 'Adventurer',
            } = req.body;

            const dungeon = {
                seed,
                filename,
                extension,
                filesize,
                uploader,
                expiration: +Date.now() + 86400000, // expire after 24 hours
            };

            await redis.sadd(
                'uploads',
                JSON.stringify(dungeon),
            );

            res.json(dungeon);
        }
    );

    return router;
};

const Redis = require('ioredis');
const winston = require('winston');
const { name: service } = require('./package.json');

module.exports = (config) => {
    const redis = new Redis(config.redis);
    const logger = winston.createLogger({
        level: config.logger.level,
        format: winston.format.json(),
        defaultMeta: { service },
        transports: [
          new winston.transports.Console({ stderrLevels: ['error', 'warn'] })
        ],
      });
    return {
        redis,
        logger,
        config,
    }
};

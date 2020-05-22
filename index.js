const express = require('express');
const { ValidationError } = require('express-validation');

const server = expressWs(express());

const config = {
    redis: process.env.REDIS_URL,
    logger: {
        level: process.env.LOG_LEVEL || 'info',
    }
}

const dependencies = require('./dependencies')(config);

server.use(require('body-parser').json());
server.use(require('./lib/daily')(dependencies));
server.use(require('./lib/multi')(dependencies));
server.use(function(err, req, res, next) {
    if (err instanceof ValidationError) {
        return res.status(err.statusCode).json(err);
    }

    return res.status(500).json(err);
});

server.listen(config.server.port);

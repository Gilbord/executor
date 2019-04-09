import logging

from aiohttp import web
import server.api

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s[LINE:%(lineno)d] %(message)s',
    )
ch.setFormatter(formatter)
logger.addHandler(ch)


def init(argv):
    app = web.Application(logger=logger)
    app.add_routes(server.api.task_routes)
    return app

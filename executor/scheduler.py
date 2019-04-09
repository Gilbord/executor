import logging
import os
import pickle
from typing import Callable
from datetime import datetime

import psycopg2
from redis import StrictRedis

logger = logging.getLogger(__name__)


class Scheduler:
    """
    Добавляет задачи в очередь выполнения.
    """

    def __init__(self):
        self.redis = StrictRedis.from_url(os.environ['REDIS_URL'])
        self.postgres = psycopg2.connect(
            dbname=os.environ['POSTGRES_DBNAME'],
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            host=os.environ['POSTGRES_HOST'],
        )

    def add_task(self, task: Callable):
        with self.postgres.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks (status, create_time) VALUES (%s, %s) RETURNING task_id;
                """,
                ("In Queue", datetime.utcnow())
            )
            self.postgres.commit()
            task_id = cursor.fetchone()[0]
            logger.debug(task_id)
            self.redis.rpush('queue', f'{task.__name__}:{task_id}'.encode('utf-8'))
            self.redis.hset('funcs', task.__name__, pickle.dumps(task, protocol=pickle.HIGHEST_PROTOCOL))
            return task_id

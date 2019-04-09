import asyncio
import logging
import os
import pickle
from concurrent.futures.process import ProcessPoolExecutor
from datetime import datetime
from time import sleep

import psycopg2
from redis import StrictRedis

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s[LINE:%(lineno)d] %(message)s',
)
ch.setFormatter(formatter)
logger.addHandler(ch)


class Worker:

    def __init__(self):
        logger.debug('Registering birth')
        self.redis = StrictRedis.from_url(os.environ['REDIS_URL'])
        self.max_workers = int(os.environ['MAX_TASK_NUMBER'])
        self.postgres = psycopg2.connect(
            dbname=os.environ['POSTGRES_DBNAME'],
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            host=os.environ['POSTGRES_HOST'],
        )

    def work(self):
        task: bytes = self.redis.lpop('queue')
        if task:
            logger.debug(str(task))
            func_name, task_id = task.decode('utf-8').split(':')
            with self.postgres.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET start_time = %s,
                        status = %s
                    WHERE task_id = %s;
                    """,
                    (datetime.utcnow(), 'RUNNING', int(task_id))
                )
                self.postgres.commit()
                func = self.redis.hget('funcs', func_name)
                start_time = datetime.now()
                pickle.loads(func)()
                cursor.execute(
                    """
                    UPDATE tasks
                    SET start_time = %s,
                        status = %s,
                        time_to_execute = %s
                    WHERE task_id = %s;
                    """,
                    (datetime.utcnow(), 'COMPLETED', (start_time - datetime.now()).microseconds, int(task_id))
                )
                self.postgres.commit()

    def start(self):
        while True:
            self.work()
            sleep(5)


def test():
    worker = Worker()
    while True:
        worker.work()
        sleep(1)


if __name__ == '__main__':
    executor = ProcessPoolExecutor(max_workers=int(os.environ['MAX_TASK_NUMBER']))
    loop = asyncio.get_event_loop()
    for _ in range(int(os.environ['MAX_TASK_NUMBER'])):
        asyncio.ensure_future(loop.run_in_executor(executor, test))
    loop.run_forever()
    #worker.start()

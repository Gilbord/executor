import logging
import os
import pickle
from datetime import datetime
from multiprocessing import Process
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
    """
    Выполняет задачи.
    """

    def __init__(self):
        logger.info('Registering birth')
        self.redis = StrictRedis.from_url(os.environ['REDIS_URL'])
        self.max_workers = int(os.environ['MAX_TASK_NUMBER'])
        self._postgres_connection = None

    def _get_postgres_connection(self):
        """
        Возвращает соединение, если оно уже установлено. В обратном случае, устанавливает его.
        Нужно, чтобы сразу подключение не создавалось, т. к. при поднятии всех image' ей docker' а
        postgresql не успевает запуститься.
        :return:
        """
        if self._postgres_connection is not None:
            return self._postgres_connection
        else:
            self._postgres_connection = psycopg2.connect(
                dbname=os.environ['POSTGRES_DBNAME'],
                user=os.environ['POSTGRES_USER'],
                password=os.environ['POSTGRES_PASSWORD'],
                host=os.environ['POSTGRES_HOST'],
            )
            return self._postgres_connection

    def work(self):
        task: bytes = self.redis.lpop('queue')
        if task:
            func_name, task_id = task.decode('utf-8').split(':')
            logger.info(f'Start running task with id: {task_id}')
            with self._get_postgres_connection().cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET start_time = %s,
                        status = %s
                    WHERE task_id = %s;
                    """,
                    (datetime.utcnow(), 'RUNNING', int(task_id))
                )
                self._get_postgres_connection().commit()
                func = self.redis.hget('funcs', func_name)
                pickled_function = pickle.loads(func)
                start_time = datetime.now()
                pickled_function()
                end_time = datetime.now()
                logger.info(f'Stop running task with id: {task_id}')
                cursor.execute(
                    """
                    UPDATE tasks
                    SET start_time = %s,
                        status = %s,
                        time_to_execute = %s
                    WHERE task_id = %s;
                    """,
                    (
                        datetime.utcnow(),
                        'COMPLETED',
                        (start_time - end_time).microseconds,
                        int(task_id)
                    )
                )
                self._get_postgres_connection().commit()


def start_worker():
    worker = Worker()
    while True:
        worker.work()
        sleep(0.1)


if __name__ == '__main__':
    for _ in range(int(os.environ['MAX_TASK_NUMBER'])):
        Process(target=start_worker).start()

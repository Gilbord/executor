import logging
import os
from datetime import datetime
from time import sleep
from typing import Dict, Union, Optional

import psycopg2
from aiohttp import web

from executor.scheduler import Scheduler

logger = logging.getLogger(__name__)


def test():
    sleep(10)
    return "123"


async def start_task(request: web.Request):
    scheduler = Scheduler()
    return web.Response(text=f'{scheduler.add_task(test)}')


def _format_date(date: datetime) -> Optional[str]:
    if not date:
        return None
    return date.strftime('%Y-%m-%d %H:%M:%S:%f')


def _get_task_info(task: tuple) -> Dict['str', Union[int, str]]:
    return {
        'task_id': task[0],
        'task_status': task[1],
        'create_time': _format_date(task[2]),
        'start_time': _format_date(task[3]),
        'time_to_execute': task[4],
    }


async def get_task_info(request: web.Request):
    with psycopg2.connect(
            dbname=os.environ['POSTGRES_DBNAME'],
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            host=os.environ['POSTGRES_HOST'],
    ) as connection:
        with connection.cursor() as cursor:
            logger.debug(request.match_info['id'])
            cursor.execute('SELECT * FROM tasks WHERE task_id=%s;', (request.match_info['id'],))
            return web.json_response(
                _get_task_info(cursor.fetchone())
            )


def fetch_by_one(cursor):
    row = cursor.fetchone()
    while row:
        yield row
        row = cursor.fetchone()


async def get_all_tasks_info(request: web.Request):
    with psycopg2.connect(
            dbname=os.environ['POSTGRES_DBNAME'],
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            host=os.environ['POSTGRES_HOST'],
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM tasks;')
            return web.json_response(
                {
                    'tasks': [_get_task_info(task) for task in fetch_by_one(cursor)],
                }
            )

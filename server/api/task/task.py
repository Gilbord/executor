import logging
from aiohttp import web

from server.utils import task_info_to_dict, fetch_by_one, get_postgre_connection
from executor.scheduler import Scheduler
from tasks.test import test


logger = logging.getLogger(__name__)


async def start_task(request: web.Request):
    """
    Добавляет задачу в очередь на выполнение.

    Example request:
        HTTP POST /tasks
    Example response:
        1

    :return: Id добавленной задачи задачи.
    """
    return web.Response(text=f'{Scheduler().add_task(test)}')


async def get_task_info(request: web.Request):
    """
    Возвращает информацию о статусе конкретной задачи.

    Example request:
        HTTP GET /tasks/1
    Example response:
        {
            'task_id': 1,
            'task_status': 'Running',
            'create_time': '2019-04-09 19:57:55:628142',
            'start_time': '2019-04-09 19:57:55:628142',
            'time_to_execute': 100,
        }

    :return: Словарь - статус о задаче.
    """
    with get_postgre_connection() as connection:
        with connection.cursor() as cursor:
            logger.debug(request.match_info['id'])
            cursor.execute('SELECT * FROM tasks WHERE task_id=%s;', (request.match_info['id'],))
            return web.json_response(
                task_info_to_dict(cursor.fetchone())
            )


async def get_latest_20_tasks_info(request: web.Request):
    """
    Возвращает информацию о статусах последних 20 задач.

    Example request:
        HTTP GET /tasks
    Example response:
        [
            {
                'task_id': 1,
                'task_status': 'Running',
                'create_time': '2019-04-09 19:57:55:628142',
                'start_time': '2019-04-09 19:57:55:628142',
                'time_to_execute': 100,
            },
        ]

    :return: Словарь - статус о задаче.
    """
    with get_postgre_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM tasks
                ORDER BY create_time DESC
                LIMIT 20;
                """
            )
            return web.json_response(
                {
                    'tasks': [task_info_to_dict(task) for task in fetch_by_one(cursor)],
                }
            )

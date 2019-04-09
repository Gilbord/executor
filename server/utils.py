import os
from datetime import datetime
from typing import Optional, Dict, Union, Iterable

import psycopg2
from psycopg2._psycopg import connection
from psycopg2.extensions import cursor


def fetch_by_one(db_cursor: cursor) -> Iterable[tuple]:
    """
    Вытаскивает все записи из БД.

    :param db_cursor: Курсор базы данных.
    :return: Запись базы данных.
    """
    row = db_cursor.fetchone()
    while row:
        yield row
        row = db_cursor.fetchone()


def format_date(date: datetime) -> Optional[str]:
    """
    Форматирует переданный объект datetime в строку.
    Если date None, то возвращает None.

    :param date: Объект datetime.
    :return: Форматированная строка - дата.
    """
    if not date:
        return None
    return date.strftime('%Y-%m-%d %H:%M:%S:%f')


def task_info_to_dict(task: tuple) -> Dict[str, Union[int, str]]:
    """
    Принимает tuple - запись из БД и конвертирует ее в словарь.

    :param task: Tuple - запись о задаче из БД.
    :return: Словарь - описание задачи.
    """
    return {
        'task_id': task[0],
        'task_status': task[1],
        'create_time': format_date(task[2]),
        'start_time': format_date(task[3]),
        'time_to_execute': task[4],
    }


def get_postgre_connection() -> connection:
    """
    Создает соединение с postgresql.
    :return: Объект - connection.
    """
    return psycopg2.connect(
        dbname=os.environ['POSTGRES_DBNAME'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        host=os.environ['POSTGRES_HOST'],
    )

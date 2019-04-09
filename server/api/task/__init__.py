from aiohttp import web

from server.api.task.task import start_task, get_task_info, get_all_tasks_info

task_routes = [
    web.post('/tasks', start_task),
    web.get('/tasks/{id}', get_task_info),
    web.get('/tasks', get_all_tasks_info)
]

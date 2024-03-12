import typing as t

from flask import current_app
from werkzeug.local import LocalProxy

if t.TYPE_CHECKING:
    from .queue import TaskQ


def _get_taskq() -> "TaskQ":
    return current_app.extensions["taskq"]


taskq: "TaskQ" = t.cast("TaskQ", LocalProxy(_get_taskq))

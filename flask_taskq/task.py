import typing as t

from flask_taskq.const import (
    DEFAULT_RETRIES,
    DEFAULT_TASK_PRIORITY,
    DEFAULT_TASK_STRATEGY,
)
from flask_taskq.types import TaskStrategy
from werkzeug.utils import import_string

if t.TYPE_CHECKING:
    from .queue import TaskQ


class TaskProxy:
    def __init__(
        self,
        queue: "TaskQ",
        func: t.Callable,
        name: str | None = None,
        priority: int = DEFAULT_TASK_PRIORITY,
        strategy: TaskStrategy = DEFAULT_TASK_STRATEGY,
        retries: int = DEFAULT_RETRIES,
    ):
        self.queue = queue
        self.func = func
        self.name = name or self.make_name(func)
        self.priority = priority
        self.strategy = strategy
        self.retries = retries

    @staticmethod
    def make_name(func: t.Callable) -> str:
        if func.__doc__:
            return func.__doc__.splitlines()[0]
        return func.__name__

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    @property
    def handler_str(self) -> str:
        return f"{self.func.__module__}.{self.func.__name__}"

    @staticmethod
    def from_handler_str(handler_str: str) -> t.Callable | "TaskProxy":
        return t.cast(t.Callable | "TaskProxy", import_string(handler_str))

    def enqueue(self, *args, **kwargs):
        return self.queue.enqueue(self, *args, **kwargs)

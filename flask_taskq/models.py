"""Database mixins."""

import typing as t

import sqlalchemy as sa
import sqlalchemy_utils as sau
from flask_taskq.task import TaskProxy
from sqlalchemy import orm
from werkzeug.utils import import_string

from .const import DEFAULT_TASK_PRIORITY
from .types import TaskStatus


class TaskMixin(sau.Timestamp):
    """Mixin for tasks table."""

    __tablename__ = "tasks"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, unique=False, nullable=False, index=True)
    status = sa.Column(
        sau.ChoiceType(TaskStatus, sa.Integer()),
        unique=False,
        nullable=False,
        index=True,
        default=TaskStatus.NEW,
    )
    handler_string = sa.Column(sa.String(), unique=False, nullable=False, index=True)
    payload = sa.Column(sa.JSON(), unique=False, nullable=True, index=False)

    runs: list["TaskRunMixinBase"]
    enqueued: list["QueueMixinBase"]

    @property
    def handler(self) -> TaskProxy | t.Callable:
        return t.cast(
            TaskProxy | t.Callable, import_string(t.cast(str, self.handler_string))
        )

    def __repr__(self) -> str:
        return f"<Task {self.id} {self.handler} {self.status}>"


class TaskRunMixinBase(sau.Timestamp):
    """Mixin for task run table."""

    __tablename__ = "task_runs"
    id = sa.Column(sa.Integer, primary_key=True)
    out = sa.Column(sa.JSON(), unique=False, nullable=True, index=False)
    err = sa.Column(sa.JSON(), unique=False, nullable=True, index=False)

    task: TaskMixin


def make_task_run_mixin(task_model: type[TaskMixin]):
    """Create task runs mixin linked to task table.

    :param task_model: Task database model.
    :returns: Mixin linked to Task database model.
    """

    class TaskRunMixin(TaskRunMixinBase):
        """Linked mixin for task run table."""

        @orm.declared_attr
        def task_id(cls):
            return sa.Column(sa.Integer, sa.ForeignKey(task_model.id), nullable=False)

        @orm.declared_attr
        def task(cls):
            return orm.relationship(task_model, backref=orm.backref("runs"))

    return TaskRunMixin


class QueueMixinBase(sau.Timestamp):
    """Mixin for queue table."""

    __tablename__ = "queue"
    id = sa.Column(sa.Integer, primary_key=True)
    priority = sa.Column(
        sa.Integer,
        unique=False,
        nullable=False,
        index=True,
        default=DEFAULT_TASK_PRIORITY,
    )
    mutex = sa.Column(sa.String(256), unique=False, nullable=True, index=True)
    retries = sa.Column(
        sa.Integer(), unique=False, nullable=False, index=False, default=0
    )

    task: TaskMixin


def make_queue_mixin(task_model: type[TaskMixin]):
    """Create queue mixin linked to task table.

    :param task_model: Task database model.
    :returns: Mixin linked to Task database model.
    """

    class QueueMixin(QueueMixinBase):
        """Linked mixin for task run table."""

        @orm.declared_attr
        def task_id(cls):
            return sa.Column(sa.Integer, sa.ForeignKey(task_model.id), nullable=False)

        @orm.declared_attr
        def task(cls):
            return orm.relationship(task_model, backref=orm.backref("enqueued"))

    return QueueMixin

"""Queue manager."""

import secrets
import traceback
import typing as t
from hashlib import sha256

from flask import Flask, current_app, g
from flask_sqlalchemy import SQLAlchemy
from flask_taskq.models import QueueMixinBase, TaskMixin, TaskRunMixinBase
from sqlalchemy.orm import scoped_session, sessionmaker

from .cli import cli
from .const import DEFAULT_RETRIES, DEFAULT_TASK_PRIORITY
from .task import TaskProxy
from .types import TaskStatus, TaskStrategy

CallableT = t.TypeVar("CallableT", bound=t.Callable)


class TaskQ:
    """TaskQ Flask extension.

    :param db: SQLAlchemy instance from Flask-SQLAlchemy package.
    :param task_mode: Task database model.
    :param task_run_model: Task run database model.
    :param queue_model: Queue database model.
    :param app: Flask application instance.
    """

    def __init__(
        self,
        db: SQLAlchemy,
        task_model: type[TaskMixin],
        task_run_model: type[TaskRunMixinBase],
        queue_model: type[QueueMixinBase],
        app: Flask | None = None,
    ):
        self.db = db
        self.task_model = task_model
        self.task_run_model = task_run_model
        self.queue_model = queue_model
        self.registered: dict[t.Callable, TaskProxy] = {}
        if app is not None:
            self.init_app(app)

    @property
    def session(self) -> scoped_session:
        """scoped_session: Separate TaskQ database session."""
        if (session := getattr(g, "taskq_session", None)) is not None:
            return session
        session = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.db.engine)
        )
        g.taskq_session = session
        return session

    def init_app(self, app: Flask):
        """Initialize application with extension.

        :param app: Flask application.
        """
        app.extensions["taskq"] = self
        app.cli.add_command(cli)

    def add_task(
        self,
        func: t.Callable,
        name: str | None = None,
        priority: int = DEFAULT_TASK_PRIORITY,
        strategy: TaskStrategy = TaskStrategy.ANY,
        retries: int = DEFAULT_RETRIES,
    ) -> TaskProxy:
        """Register task.

        :param func: Task function.
        :param name: Task name.
        :param priority: Task priority.
        :param strategy: Task strategy.
        :param retries: Task retries.
        :returns: TaskProxy instance.
        """
        self.registered[func] = TaskProxy(self, func, name, priority, strategy, retries)
        return self.registered[func]

    def task(
        self,
        name: str | None = None,
        priority: int = DEFAULT_TASK_PRIORITY,
        strategy: TaskStrategy = TaskStrategy.ANY,
        retries: int = DEFAULT_RETRIES,
    ) -> t.Callable[[t.Callable], TaskProxy]:
        """Decorator to register task.

        :param name: Task name.
        :param priority: Task priority.
        :param strategy: Task strategy.
        :param retries: Task retries.
        :returns: Decorator to add task."""

        def decorator(func: t.Callable) -> TaskProxy:
            """Decorator to register task.

            :param func: Function to register.
            :returns: TaskProxy instance.
            """
            return self.add_task(func, name, priority, strategy, retries)

        return decorator

    def get_task_proxy(self, task: t.Callable | TaskProxy) -> TaskProxy:
        """Converts task function to task proxy if needed.

        Used for situations when task decorator wasn't used, so behind handler_string
        stored actual task function, not task proxy object.

        :param task: Task.
        :returns: TaskProxy.
        """
        if isinstance(task, TaskProxy):
            return task
        return self.registered[task]

    def get_task(self, task_id: int, for_update: bool = False) -> TaskMixin | None:
        """Get task instance by task id.

        :param task_id: Task id.
        :returns: Task instance or None.
        """
        query = self.session.query(self.task_model).filter(
            self.task_model.id == task_id
        )
        if for_update:
            query = query.with_for_update(skip_locked=False)
        return query.first()

    def tasks(self, all_: bool = False) -> t.Sequence[TaskMixin]:
        query = self.session.query(self.task_model)
        if not all_:
            query = query.filter(self.task_model.enqueued != None)
        return query.all()

    def restart(self, task: TaskMixin) -> QueueMixinBase:
        return self.enqueue(
            task.handler, *task.payload["args"], **task.payload["kwargs"]  # type: ignore
        )

    def cancel(self, task: TaskMixin) -> bool:
        if task.status not in (TaskStatus.NEW, TaskStatus.RETRY):
            return False
        task.status = TaskStatus.CANCELLED  # type: ignore
        self.session.add(task)
        for to_delete in task.runs:
            self.session.delete(to_delete)
        self.session.commit()
        return True

    def enqueue(self, task: TaskProxy | t.Callable, *args, **kwargs) -> QueueMixinBase:
        task = self.get_task_proxy(task)
        task_instance = self.task_model(
            name=task.name,
            handler_string=task.handler_str,
            payload={"args": args, "kwargs": kwargs},
        )
        enqueued_task = self.queue_model(
            task=task_instance,
            priority=task.priority,
            mutex=sha256(secrets.token_bytes()).hexdigest()
            if task.strategy == TaskStrategy.ANY
            else sha256(f"{task.name}{task.handler_str}".encode()).hexdigest(),
        )
        self.session.add(task_instance)
        self.session.add(enqueued_task)
        self.session.commit()
        return enqueued_task

    def pop(self) -> tuple[QueueMixinBase | None, t.Sequence[QueueMixinBase]]:
        enqueued_tasks: list[QueueMixinBase] = (
            self.session.query(self.queue_model)
            .filter(
                self.queue_model.mutex
                == self.session.query(self.queue_model.mutex)
                .filter(self.task_model.status.in_((TaskStatus.NEW, TaskStatus.RETRY)))
                .join(self.task_model, self.task_model.id == self.queue_model.task_id)
                .group_by(self.queue_model.mutex)
                .order_by(self.queue_model.priority.desc())
                .limit(1)
                .scalar_subquery(),
                self.task_model.status.in_((TaskStatus.NEW, TaskStatus.RETRY)),
            )
            .join(self.task_model, self.task_model.id == self.queue_model.task_id)
            .order_by(self.queue_model.priority.desc(), self.queue_model.created.desc())
            .with_for_update(skip_locked=True)
        ).all()

        if len(enqueued_tasks) <= 0:
            return None, []

        task_proxy = self.get_task_proxy(enqueued_tasks[0].task.handler)
        strategy = task_proxy.strategy
        if strategy == TaskStrategy.ANY:
            enqueued_task = enqueued_tasks.pop(0)
            enqueued_tasks.clear()
        else:
            enqueued_task = enqueued_tasks.pop(
                0 if strategy in (TaskStrategy.FIRST, TaskStrategy.UNIQUE) else -1
            )
            for to_update in enqueued_tasks:
                to_update.task.status = (
                    TaskStatus.BLOCKED  # type: ignore[assignment]
                    if strategy == TaskStrategy.UNIQUE
                    else TaskStatus.CANCELLED
                )
                self.session.add(to_update.task)
                if strategy != TaskStrategy.UNIQUE:
                    self.session.delete(to_update)

        enqueued_task.task.status = TaskStatus.PROGRESS  # type: ignore[assignment]
        self.session.add(enqueued_task)

        self.session.commit()

        return enqueued_task, enqueued_tasks

    def run(self) -> TaskRunMixinBase | None:
        enqueued_task, blocked_enqueued_tasks = self.pop()
        if enqueued_task is None:
            current_app.logger.info("No tasks to proceed, skipping.")
            return None

        if blocked_enqueued_tasks:
            current_app.logger.info(
                "Processing task %s with blocking %s",
                enqueued_task.task,
                ", ".join(str(blocked.task) for blocked in blocked_enqueued_tasks),
            )
        else:
            current_app.logger.info(
                "Processing task %s", enqueued_task.task
            )

        try:
            # NOTE: Run each task in separate application context to ensure
            #       that all callbacks and other things are done right.
            with current_app.app_context():
                result = enqueued_task.task.handler(
                    *enqueued_task.task.payload["args"],  # type: ignore
                    **enqueued_task.task.payload["kwargs"],  # type: ignore
                )
        except Exception as exc:
            current_app.logger.exception(exc)
            task_run = self.task_run_model(
                task=enqueued_task.task, err={"traceback": traceback.format_exc()}
            )
            self.session.add(task_run)
            task_proxy = self.get_task_proxy(enqueued_task.task.handler)
            if task_proxy.retries < 0 or enqueued_task.retries < task_proxy.retries:
                enqueued_task.task.status = TaskStatus.RETRY  # type: ignore[assignment]
                enqueued_task.retries += 1  # type: ignore[assignment]
                self.session.add(enqueued_task)
                current_app.logger.info(
                    "Task %s processing falied, will retry.", enqueued_task.task
                )
            else:
                current_app.logger.info(
                    "Task %s processing failded, finishing as failed.",
                    enqueued_task.task,
                )
                enqueued_task.task.status = TaskStatus.FAILED  # type: ignore[assignment]
                self.session.delete(enqueued_task)
            self.session.add(enqueued_task.task)
        else:
            task_run = self.task_run_model(task=enqueued_task.task, out=result)
            enqueued_task.task.status = TaskStatus.COMPLETED  # type: ignore[assignment]
            self.session.add(task_run)
            self.session.add(enqueued_task.task)
            self.session.delete(enqueued_task)

        for to_unlock in blocked_enqueued_tasks:
            to_unlock.task.status = TaskStatus.NEW  # type: ignore[assignment]
            self.session.add(to_unlock.task)

        self.session.commit()

        return task_run

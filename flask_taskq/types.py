"""Types of the package."""

import typing as t
from enum import Enum


class TaskStatus(int, Enum):
    """Task status."""

    #: New task.
    NEW = 0
    #: Retry.
    RETRY = 1
    #: Waiting for next stage.
    # PENDING = 2
    #: Blocked by another task.
    BLOCKED = 3
    #: Task in progress.
    PROGRESS = 4
    #: Task successfully completed.
    COMPLETED = 5
    #: Task failed with error.
    FAILED = 6
    #: Task was cancelled.
    CANCELLED = 7


class TaskStrategy(int, Enum):
    """Task processing strategy."""

    #: All added tasks of this handler will be processed without blocking each other.
    ANY = 0
    #: Only one task of that handler can be processed in one period of time, others will be blocked.
    UNIQUE = 1
    #: Only latest added task of this handler will be processed, others will be cancelled.
    LAST = 2
    #: Only first added task of this handler will be processed, others will be cancelled.
    FIRST = 3


class Payload(t.TypedDict):
    args: tuple[t.Any, ...]
    kwargs: dict[t.Any, t.Any]


class TaskError(t.TypedDict):
    traceback: str

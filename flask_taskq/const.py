"""Package constants."""

from flask_taskq.types import TaskStrategy

#: Default task priotiry.
DEFAULT_TASK_PRIORITY: int = 0
#: Default task strategy.
DEFAULT_TASK_STRATEGY: TaskStrategy = TaskStrategy.ANY
#: Default retries count.
DEFAULT_RETRIES: int = 0

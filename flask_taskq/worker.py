import time
from enum import Enum
from flask import current_app

from .globals import taskq


class WorkerType(str, Enum):
    SYNC = "sync"


class Worker:
    def run(self):
        current_app.logger.info("Starting SYNC taskq worker.")
        while True:
            taskq.run()
            time.sleep(0.25)


workers: dict[WorkerType, type[Worker]] = {WorkerType.SYNC: Worker}

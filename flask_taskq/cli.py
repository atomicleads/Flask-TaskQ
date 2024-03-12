"CLI for TaskQ."

import sys

import click
from flask.cli import AppGroup
from prettytable import PrettyTable

from .globals import taskq
from .worker import WorkerType, workers

cli = AppGroup("taskq")


@cli.command("list")
@click.option(
    "-a",
    "--all",
    "all_",
    required=False,
    is_flag=True,
    default=False,
    show_default=True,
    help="Show all tasks, with already completed.",
)
def list_tasks(all_: bool):
    """Show tasks."""
    table = PrettyTable(
        ["id", "name", "status", "handler", "runs","enqueued", "creared", "updated"]
    )
    for task in taskq.tasks(all_):
        table.add_row(
            [
                task.id,
                task.name,
                task.status,
                task.handler_string,
                len(task.runs),
                bool(task.enqueued),
                task.created,
                task.updated,
            ]
        )
    click.echo(table.get_string())


@cli.command("show")
@click.argument("task_id", required=True)
def show_task(task_id: int):
    task = taskq.get_task(task_id)
    if not task:
        click.echo(f"Task {task_id} not found.", err=True)
        sys.exit(1)
    task_table = PrettyTable(
        ["id", "name", "status", "handler", "runs","enqueued","payload", "creared", "updated"]
    )
    task_table.add_row(
        [
            task.id,
            task.name,
            task.status,
            task.handler_string,
            len(task.runs),
            bool(task.enqueued),
            task.payload,
            task.created,
            task.updated,
        ]
    )
    click.echo(task_table.get_string())
    runs_table = PrettyTable(["at", "out", "err"])
    for run in task.runs:
        runs_table.add_row([run.created, run.out, run.err])
    click.echo(runs_table.get_string())


@cli.command("restart")
@click.argument("task_id", required=True)
def restart_task(task_id: int):
    """Restart task."""
    task = taskq.get_task(task_id, True)
    if not task:
        click.echo(f"Task {task_id} not found.", err=True)
        sys.exit(1)
    new_task = taskq.restart(task)
    click.echo(f"Task {task.id} restarted as {new_task.id}")


@cli.command("cancel")
@click.argument("task_id", required=True)
def cancel_task(task_id: int):
    """Cancel task."""
    task = taskq.get_task(task_id, True)
    if not task:
        click.echo(f"Task {task_id} not found.", err=True)
        sys.exit(1)
    if taskq.cancel(task):
        click.echo(f"Task {task.id} successfully cancelled.")
    else:
        click.echo(f"Failed to cancel task {task.id}.", err=True)
        sys.exit(1)


@cli.group("worker")
def worker():
    """Worker manegement."""
    pass


@worker.command("run")
@click.option(
    "-t",
    "--type",
    "type_",
    type=click.Choice(list(WorkerType), case_sensitive=False),
    required=False,
    default=WorkerType.SYNC,
)
def start_worker(type_: WorkerType):
    """Run worker."""
    workers[type_]().run()

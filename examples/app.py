#!/usr/bin/env python

from os import path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_taskq import TaskMixin, TaskQ, make_queue_mixin, make_task_run_mixin
from flask_taskq.types import TaskStrategy
from sqlalchemy.sql import text

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{}".format(
    path.join(path.dirname(path.abspath(__name__)), "db.sqlite3")
)
db = SQLAlchemy(app)


class Task(db.Model, TaskMixin):
    pass


class TaskRun(db.Model, make_task_run_mixin(Task)):
    pass


class Queue(db.Model, make_queue_mixin(Task)):
    pass


taskq = TaskQ(db, Task, TaskRun, Queue, app=app)


@taskq.task("test", strategy=TaskStrategy.UNIQUE, retries=2)
def test1():
    """EHLO with retries"""
    print("EHLO")


def test2(word: str = "World"):
    "Just hello world"
    print(f"Hello, {word}!")


@taskq.task("breakdb")
def test3():
    "Trying to break database."
    db.session.execute(text("SELECT foo FROM bar;"))
    db.session.commit()
    db.session.rollback()
    db.session.remove()
    db.session.commit()


taskq.add_task(test2)


@app.teardown_appcontext
def on_teardown_appcontext(_):
    print("Teardown that will be called on every task run.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

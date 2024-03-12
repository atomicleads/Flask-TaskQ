Quickstart
==========

Here is some simple tutorial how to get started with `Flask-TaskQ` after the installation.

Import and initialize
---------------------

First of all you need to import and initialize extension with your application.

.. code:: python

   from flask import Flask
   from flask_sqlalchemy import SQLAlchemy
   from flask_taskq import TaskMixin, make_queue_mixin, make_task_run_mixin, TaskQ


   # Initialize application and Flask-SQLAlchemy
   app = Flask(__name__)
   app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
   db = SQLAlchemy(app)


   # Define models used by TaskQ: Task, TaskRun and Queue.
   class Task(db.Model, TaskMixin):
       pass


   class TaskRun(db.Model, make_task_run_mixin(Task)):
       pass


   class Queue(db.Model, make_queue_mixin(Task)):
       pass


   # Finally, initialize Flask-TaskQ extension.
   taskq = TaskQ(db, Task, TaskRun, Queue, app=app)


Define tasks
------------

After you initialized extension you can define tasks.

.. code:: python

   # Tasks can be defined with decorator.
   @taskq.task("Example task")
   def foo():
       return "bar"

    def bar(r="foo"):
        return r

    # And also added with add_task method.
    taskq.add_task(bar)


Enqueue task
------------

Defined tasks can be enqueued to process.

.. note::

    Please note that enqueue operation is available only
    within the application context of Flask application.

.. code:: python

   # Tasks defined with decorator can be enqueued with .enqueue method of the task.
   foo.enqueue()

   # Tasks defined without decorator can be enqueued with .enqueue method of extension object.
   taskq.enqueue(bar)


Start queue worker
------------------

After tasks been enqueued they can be processed by queue worker.
Queue worker can be started with command:

.. code:: bash

   flask taskq worker run

This command will start worker and process all tasks in queue.


Full Example
------------

Here is full example from `examples` directory of the project repository.

.. include:: ../examples/app.py
    :code: python

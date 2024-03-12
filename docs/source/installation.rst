Installation
============

Installation from PyPI
----------------------

This is the most common way to install `Flask-TaskQ` extension:

.. code:: bash

   pip install Flask-TaskQ

This will install extension and all it's dependencies:

* Flask
* Flask-SQLAlchemy
* prettytable(will be removed as required dependency in future versions)

Your application also need database backend, this is supported database backends:

* sqlite is supported, but not recommended
* For PostgreSQL install `psycopg2` package.

Building from source
--------------------

To install package from source, first of all you need to clone project repository:

.. code:: bash

   git clone https://github.com/TitaniumHocker/Flask-TaskQ.git Flask-TaskQ

Then you can install it from source:

.. code:: bash

   pip install ./Flask-TaskQ

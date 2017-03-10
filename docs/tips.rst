####
Tips
####

Coala
=====

Coala is a great tool for linting all languages. We use it here in lftools for
linting this project and can be launched simply with python-tox as long as
Python 3 is available on the system.

.. code-block:: bash

    tox -ecoala

Sometimes running Coala without tox such as for running in interactive mode
could be handy. In this case it is necessary to install Coala. The recommended
way to setup Coala is to use a Python VirtualEnv. If possible using a script
called virtualenvwrapper is recommended as it makes it very simple to manage
local virtualenvs.

Requirements
------------

* Python 3
* Python VirtualEnv
* Python VirtualEnvWrapper

Install Coala
-------------

.. note::

    Some distros have a package called *coala* available however do not confuse
    this package with python-coala which is an entirely different piece of
    software.

Using virtualenv is the way this guide recommends setting up on a local system
and will assume VirtualEnvWrapper is available. To install Coala run the
following commands.

.. code-block:: bash

    mkvirtualenv --python=/usr/bin/python3 coala
    pip install coala coala-bears
    coala --help

In future runs in a new shell you can activate the existing coala virtualenv as
follows.

.. code-block:: bash

    workon coala
    coala --help

Setting up Coala a Project
--------------------------

In some cases we may want to setup coala for a new project that wants to start
linting their project. We recommend using python-tox to manage a Coala setup
for any projects.

**Requirements**

* Python 3
* Python VirtualEnv
* Python Tox

Once requirements are met configure the project with a tox.ini and a .coafile
file. Below are examples of .coafile and tox.ini as defined by lftools. Inside
the tox.ini file the interesting bits are under [testenv:coala].

**.coafile**

.. literalinclude:: ../.coafile
    :language: ini

**tox.ini**

.. literalinclude:: ../tox.ini
    :language: ini

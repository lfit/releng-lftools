############
Installation
############

.. note::

    LFtools requires python3 (3.6+) virtual environment.
    https://virtualenv.pypa.io/en/stable/.
    Not using a virtualenv can have serious negative side effects!


For Install
===========

LFTools is available on pypi. LFtools has migrated to python3, ensure python3
is available your system. To install LFTools, create a virtualenv,
with `pip3 install lftools` in your shell.


For Development
===============

Often during development you want to run tests and/or
try code out locally as you change it.  To do this you
need the installation of LFTools to be your local git repo.
After doing `pip3 install -r requirements.txt` issue the
command `pip3 install -e .`

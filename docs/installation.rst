############
Installation
############

.. note::

    The Linux Foundation strongly recommends that you have a python
    virtual environment to work in. https://virtualenv.pypa.io/en/stable/.
    Not using a virtualenv can have serious negative side effects!


For Install
===========

LFTools is available on pypi.  To install, after making a virtualenv,
do `pip install lftools` in your shell.

For Development
===============

Often during development you want to run tests and/or
try code out locally as you change it.  To do this you
need the installation of LFTools to be your local git repo.
After doing `pip install -r requirements.txt` issue the
command `pip install -e .`

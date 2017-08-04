############
Installation
############

.. note::

    The Linux Foundation strongly recommendeds that you have a python
    virtual environment to work in. https://virtualenv.pypa.io/en/stable/.
    Not using a virtualenv can have serious negative side effects!


For Use
=======

LFTools is a simple python library with an accompanying
`requirements.txt` file in the root of the project. You can
install these by doing `pip install -r requirements.txt`.
After the dependencies install do `pip install .` in the
root of the project. At that point the library is ready
to use and you can check by issuing the command `lftools`
in your shell.


For Development
===============

Often during development you want to run tests and/or
try code out locally as you change it.  To do this you
need the installation of LFTools to be your local git repo.
After installing the requirements as noted above issue the
command `pip install -e .`
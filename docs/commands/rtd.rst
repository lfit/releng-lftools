***********
ReadTheDocs
***********

.. program-output:: lftools rtd --help

Commands
========

project-list
------------

.. program-output:: lftools rtd project-list --help

project-details
---------------

.. program-output:: lftools rtd project-details --help


project-version-list
--------------------

.. program-output:: lftools rtd project-version-list --help


project-version-details
-----------------------

.. program-output:: lftools rtd project-version-details --help


project-version-update
----------------------

.. program-output:: lftools rtd project-version-update --help


project-create
--------------

.. program-output:: lftools rtd project-create --help


project-build-list
------------------

.. program-output:: lftools rtd project-build-list --help


project-build-details
---------------------

.. program-output:: lftools rtd project-build-details --help


project-build-trigger
---------------------

.. program-output:: lftools rtd project-build-trigger --help



API requires a [rtd] section in ~/.config/lftools/lftools.ini:

.. code-block:: bash

   [rtd]
   token = REDACTED
   endpoint = https://readthedocs.org/api/v3/


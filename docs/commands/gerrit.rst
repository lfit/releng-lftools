******
Gerrit
******

.. program-output:: lftools gerrit --help

Commands
========

list-project-permissions
------------------------

.. program-output:: lftools gerrit list-project-permissions --help


addgitreview
------------

.. program-output:: lftools gerrit addgitreview --help


addgithubrights
---------------

.. program-output:: lftools gerrit addgithubrights --help


addfile
-------

.. program-output:: lftools gerrit addfile --help


createproject
-------------

.. program-output:: lftools gerrit createproject --help


addinfojob
----------
.. program-output:: lftools gerrit addinfojob --help


.. note::

        Gerrit API methods require configuration in lftools.ini
        in a global [gerrit] section.
        support for [gerrit.umbrella.tld] exists as well
        signed_off_by required to push changes.


.. code-block:: none

     [gerrit]
     username = lfid
     password = password
     signed_off_by = Your Name <your@email.org>

     [gerrit.opnfv.org]
     username = lfid
     password = password
     signed_off_by = Your Name <your@email.org>


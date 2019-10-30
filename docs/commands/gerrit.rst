******
Gerrit
******

.. program-output:: lftools gerrit --help

Commands
========

createproject
-------------

.. program-output:: lftools gerrit createproject --help


prepareproject
--------------

.. program-output:: lftools gerrit prepareproject --help


addinfojob
----------
.. program-output:: lftools gerrit addinfojob --help


addinfofile
-----------
.. program-output:: lftools gerrit addinfofile --help



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


********
Infofile
********

.. program-output:: lftools infofile --help

Commands
========

check-votes
-----------

 .. program-output:: lftools infofile check-votes --help

get-committers
--------------

 .. program-output:: lftools infofile get-committers --help

sync-committers
---------------

 .. program-output:: lftools infofile sync-committers --help


Creating an info file requires a connection to the VPN

create-info-file
----------------

 .. program-output:: lftools infofile create-info-file --help



API for check votes requires a [github] section in ~/.config/lftools/lftools.ini:

.. code-block:: bash

   [github]
   token = REDACTED


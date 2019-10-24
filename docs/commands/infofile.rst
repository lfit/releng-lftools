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
and a working openldap configuration


.. code-block:: bash

    $ cat /etc/openldap/ldap.conf
    TLS_REQCERT never
    or
    prereqs: For ldap lookups to work you must be on the VPN and have the cert to get the cert: log in to any collab system and grab /etc/ipa/ca.crt in /etc/openldap/ldap.conf, add 'TLS_CACERT /path/to/ipa.ca'


create-info-file
----------------

 .. program-output:: lftools infofile create-info-file --help



API for check votes requires a [github] section in ~/.config/lftools/lftools.ini:

.. code-block:: bash

   [github]
   token = REDACTED


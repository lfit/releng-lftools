*******
Lfidapi
*******

.. program-output:: lftools lfidapi --help

Commands
========

create-group
------------

.. program-output:: lftools lfidapi create-group --help

invite
-------

.. program-output:: lftools lfidapi invite --help

search-members
--------------

.. program-output:: lftools lfidapi search-members --help


user
----

.. program-output:: lftools lfidapi user --help

match-ldap-to-info
------------------

.. program-output:: lftools lfidapi match-ldap-to-info --help


API requires an [lfid] section in ~/.config/lftools/lftools.ini:

.. code-block:: bash

   [lfid]
   clientid = lf-releng-jenkins
   client_secret = REDACTED_SEE_SHARED_PASSWORD_STORAGE
   refresh_token = REDACTED_SEE_SHARED_PASSWORD_STORAGE
   token_uri = https://identity.linuxfoundation.org/oauth2/token
   url = https://identity.linuxfoundation.org/rest/auth0/og/

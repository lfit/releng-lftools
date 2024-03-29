******
Gerrit
******

.. program-output:: lftools gerrit --help

Commands
========

list-project-permissions
------------------------

.. program-output:: lftools gerrit list-project-permissions --help


list-project-inherits-from
--------------------------

.. program-output:: lftools gerrit list-project-inherits-from --help


abandonchanges
--------------

.. program-output:: lftools gerrit abandonchanges --help

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


create-saml-group
-----------------

.. program-output:: lftools gerrit create-saml-group --help


addinfojob
----------
.. program-output:: lftools gerrit addinfojob --help


.. note::

        Gerrit API methods require configuration in lftools.ini
        in a global [gerrit] section.
        support for [gerrit.umbrella.tld] exists as well
        signed_off_by required to push changes.
        Projects that do not allow self merge will require
        as project.example.org.second section for submission
        of their .gitreview on project creation.


.. code-block:: none

     [gerrit.example.org]
     username = lfid
     password = password
     signed_off_by = Your Name <your@email.org>

     [gerrit.example.org.second]
     username = lfid2
     password = password2
     signed_off_by = Your Name <your@email.org>

addmavenconfig
--------------
.. program-output:: lftools gerrit addmavenconfig --help


An example of the lftools.ini entry for a Gerrit server making use of a full
configuration:

.. code-block:: none

     [gerrit.example.org]
     username = lfid
     password = password
     signed_off_by = Your Name <your@email.org>
     endpoint = https://gerrit.example.org/
     default_servers = releases,snapshots,staging,site
     nexus3 = nexus3.example.org
     nexus3_ports = 10001,10002,10003,10004
     additional_credentials = {"docker.io": "dockerhub-cred", "nexus-iq": "nexus-iq-cred"}

.. _nexus:

*****
Nexus
*****

.. program-output:: lftools nexus --help

.. _nexus-commands:

Commands
========

.. contents:: Nexus Commands
    :local:

.. _nexus-create:

create
------

.. program-output:: lftools nexus create --help

.. _nexus-repo:

repo
^^^^

.. program-output:: lftools nexus create repo --help

.. _nexus-reorder-staged-repos:

reorder-staged-repos
--------------------

.. program-output:: lftools nexus reorder-staged-repos --help

.. _nexus-docker:

docker
------

.. program-output:: lftools nexus docker --help

.. _nexus-list:

For ``nexus docker`` commands, a settings.yaml file can be used, as with the
older commands. However, the preferred way to authorize is using an lftools.ini
file, and providing the server address using the ``--server`` option. The
config file should be located at $HOME/.config/lftools/lftools.ini.

list
^^^^

.. program-output:: lftools nexus docker list --help

delete
^^^^^^

.. program-output:: lftools nexus docker delete --help

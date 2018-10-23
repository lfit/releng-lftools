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

While a settings.yaml file is still supported for ``nexus docker`` commands,
the preferred way to login is to use an lftools.ini file, and provide the
server address using the ``--server`` option. The config file should be at
$HOME/.config/lftools/lftools.ini.

.. _nexus-docker-delete:

delete
^^^^^^

.. program-output:: lftools nexus docker delete --help

.. _nexus-docker-list:

list
^^^^

.. program-output:: lftools nexus docker list --help

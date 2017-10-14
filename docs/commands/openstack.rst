*********
OpenStack
*********

Requires a `pip install lftools[openstack]` to activate this command.

.. program-output:: lftools openstack --help

Commands
========

.. contents:: OpenStack Commands
    :local:

image
-----

.. program-output:: lftools openstack --os-cloud docs image --help

cleanup
^^^^^^^

The intent of this command is to automatically cleanup old images in the cloud.
The OpenDaylight project has 2 clouds, a Private Cloud and a Public cloud which
needs the `--clouds` option to automatically remove the same images from
more than one cloud simultaneously.

.. program-output:: lftools openstack --os-cloud docs image cleanup --help

list
^^^^

.. program-output:: lftools openstack --os-cloud docs image list --help

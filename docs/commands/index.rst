########
Commands
########

lftools is a collection of scripts written directly in python or externally via
bash.

lftools the top level command supports a debug flag which can be enabled via
``lftools --debug`` preceding any commands or via environment variable
``DEBUG=True`` which will print extra information if available.

It supports the following commands:

.. toctree::
    :maxdepth: 2

    config
    deploy
    dco
    license
    nexus
    openstack
    sign
    version

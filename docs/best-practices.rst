##############
Best Practices
##############

Coala
=====

Coala is a great tool for linting all languages. We use it here in lftools for
linting this project. The easiest way to run coala is with python-tox and
requires Python 3 installed on the system.

.. code-block:: bash

    tox -ecoala

Sometimes running Coala without tox such as for running in interactive mode
could be handy. In this case install Coala. The recommended
way to setup Coala is to use a Python VirtualEnv. We recommend using a script
called virtualenvwrapper as it makes it simple to manage local virtualenvs.

Requirements
------------

* Python 3
* Python VirtualEnv
* Python VirtualEnvWrapper

Install Coala
-------------

.. note::

    Some distros have a package called *coala* available but do not confuse
    this package with python-coala which is an entirely different piece of
    software.

Using virtualenv is the way this guide recommends setting up on a local system
and will assume VirtualEnvWrapper is available. To install Coala run the
following commands.

.. code-block:: bash

    mkvirtualenv --python=/usr/bin/python3 coala
    pip install coala coala-bears
    coala --help

In future runs in a new shell you can activate the existing coala virtualenv as
follows.

.. code-block:: bash

    # Re-activate coala virtualenv
    workon coala
    # Run the coala command
    coala --help

Setting up Coala a Project
--------------------------

In some cases we may want to setup coala for a new project that wants to start
linting their project. We recommend using python-tox to manage a Coala setup
for any projects.

**Requirements**

* Python 3
* Python VirtualEnv
* Python Tox

With requirements installed configure the project with a tox.ini and a .coafile
file. Below are examples of .coafile and tox.ini as defined by lftools. Inside
the tox.ini file the interesting bits are under [testenv:coala].

**.coafile**

.. literalinclude:: ../.coafile
    :language: ini

**tox.ini**

.. literalinclude:: ../tox.ini
    :language: ini


Jenkins Job Builder
===================

Passing parameters to shell scripts
-----------------------------------

There are 2 ways to pass parameters into scripts:

1) JJB variables in the format {var}
2) Environment variables in the format ${VAR}

We recommend avoiding using method 1 (Pass JJB variables) into shell scripts
and instead always use method 2 (Enviornment variables). This makes
troubleshooting JJB errors easier and does not require escaping curly braces.

This method requires 2 steps:

1) Declare a parameter section
2) Use the parameter in shell script

The benefit of this method is that parameters will always be at the top
of the job page and when clicking the Build with Parameters button in Jenkins
we can see the parameters before running the job. We can review the
parameters retro-actively by visiting the job parameters page
``job/lastSuccessfulBuild/parameters/``.

Usage of config-file-provider
-----------------------------

When using the config-file-provider plugin in Jenkins to provide a config file.
We recommend using a macro so that we can configure the builder to
remove the config file as a last step. This ensures
that credentials do not exist on the system for longer than it needs to.

ship-logs example:

.. code-block:: yaml

    - builder:
        name: lf-ship-logs
        builders:
          - config-file-provider:
              files:
                - file-id: 'jenkins-log-archives-settings'
                  variable: 'SETTINGS_FILE'
          - shell: !include-raw:
              - ../shell/logs-get-credentials.sh
          - shell: !include-raw:
              - ../shell/lftools-install.sh
              - ../shell/logs-deploy.sh
          - shell: !include-raw:
              - ../shell/logs-clear-credentials.sh
          - description-setter:
              regexp: '^Build logs: .*'

In this example the script logs-deploy requires a config file to authenticate
with Nexus to push logs up. We declare a macro here so that we can ensure that
we remove credentials from the system after the scripts
complete running via the logs-clear-credentials.sh script. This script contains
3 basic steps:

1. Provide credentials via config-file-provider
2. Run the build scripts in this case lftools-install.sh and logs-deploy.sh
3. Remove credentials provided by config-file-provider

Preserving Objects in Variable References
-----------------------------------------

JJB has an option to preserve a data structure object when you want to pass it to a template.
This is documented at:
https://docs.openstack.org/infra/jenkins-job-builder/definition.html#variable-references.

One thing that is not explicitly covered is the format of the variable name that you pass the object to.
When you use the `{obj:key}` notation to preserve the original data structure object, it will not work
if the variable name has a dash `-` in it.  The standard that we follow, and that we recommend, is to use
an uderscore `_` where you would have used a dash.

Example:
  code-block:: yaml
    - triggers:
       - lf-infra-github-pr-trigger:
           trigger-phrase: '^remerge$'
           only-trigger-phrase: true
           status-context: 'JJB Merge'
           permit-all: false
           github-hooks: true
           github-org: '{github-org}'
           github_pr_whitelist: '{obj:github_pr_whitelist}'
           github_pr_admin_list: '{obj:github_pr_admin_list}'

In the above example not the use of underscores in `github_pr_admin_list` and `github_pr_admin_list`.

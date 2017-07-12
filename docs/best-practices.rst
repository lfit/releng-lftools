##############
Best Practices
##############

Code Review
===========

.. Listing Code Ceview first as it is incredibly important.

Ideally all patches that go into a project repo should be code reviewed by
someone other than the original author. Code review is a very good way to both
learn from others as well as improve code quality and we highly recommend
everyone participate in code review regardless of if you are an active
committer on a project or not.

Below provides a simple checklist of common things that code reviewers should
look out for (Patch submitters are encouraged to self-review as well to ensure
that they are not hitting any of these):

- Does the Git commit message sufficiently describes the change?
  (Refer to: https://chris.beams.io/posts/git-commit/)
- Are there any typos?
- Are imports alphabetical and sectioned off by stdlib, 3rdparty, and local?
- Are functions / methods organized alphabetically?
  (or categorized alphabetically)
- Does the change need unit test?
  (Yes, it probably does!)
- Does the change need documentation?
  (Most likely!)
- Does every function added have function docs?
  (javadoc, pydoc, whatever language equivalent is)
- Does it pass linting?

Google posted an interesting blog on effective code review and how to spend both
your own and your reviewers' time wisely.

https://testing.googleblog.com/2017/06/code-health-too-many-comments-on-your.html


Coala
=====

Coala is a great tool for linting all languages. We use it here in lftools for
linting this project and can be launched simply with python-tox as long as
Python 3 is available on the system.

.. code-block:: bash

    tox -ecoala

Sometimes running Coala without tox such as for running in interactive mode
could be handy. In this case it is necessary to install Coala. The recommended
way to setup Coala is to use a Python VirtualEnv. If possible using a script
called virtualenvwrapper is recommended as it makes it very simple to manage
local virtualenvs.

Requirements
------------

* Python 3
* Python VirtualEnv
* Python VirtualEnvWrapper

Install Coala
-------------

.. note::

    Some distros have a package called *coala* available however do not confuse
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

    workon coala
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

Once requirements are met configure the project with a tox.ini and a .coafile
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

In a shell script there are 2 types of parameters that can be passed in via JJB.

1) JJB variables in the format {var}
2) Environment variables in the format ${VAR}

One of the issues one may run into when using JJB variables in shell scripts is
that curly braces ``{var}`` need to be escaped for not JJB variables such as
``${VAR}`` which would become ``${{VAR}}`` and would not pass ShellCheck. It
also makes scripts more difficult to debug when something has gone wrong.

Instead it is best practice to not pass in JJB variables into shell scripts and
instead always use Enviornment variables when a parameter is needed. This method
requires 2 steps:

1) Declare a parameter section
2) Use the parameter in shell script

What is nice about this is since parameters in a job are listed at the top of
the job page as well as when running a build we can also very clearly see what
parameters are being passed into the job. We can review the parameters
retro-actively by visiting the job parameters page
``job/lastSuccessfulBuild/parameters/``.

Usage of config-file-provider
-----------------------------

When using the config-file-provider plugin in Jenkins to provide a config file
we should create a macro such that the builder that needs the config file
removes the config file immediately after it is done using it. This ensures
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
the credentials are removed from the system immediately after the scripts are
complete running via the logs-clear-credentials.sh script. This script contains
3 basic steps:

1. Provide credentials via config-file-provider
2. Run the build scripts in this case lftools-install.sh and logs-deploy.sh
3. Remove credentials provided by config-file-provider

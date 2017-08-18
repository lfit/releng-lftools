##############
Best Practices
##############

Code Review
===========

.. Code Review is incredibly important so list it first.

All patches that go into a project repo need to be code reviewed by someone
other than the original author. Code review is a great way to both learn from
others as well as improve code quality and we highly recommend everyone code
review patches regardless of if you are an active committer on a project or not.

Below provides a simple checklist of common items that code reviewers should
look out for (Patch submitters can use this to self-review as well to ensure
that they are not hitting any of these):

**General**

- Does the Git commit message sufficiently describes the change?
  (Refer to: https://chris.beams.io/posts/git-commit/)
- Does the commit message have an 'Issue: <someissue>' in the footer and not
  in the subject line or body?
- Are there any typos?
- Are all code review comments addressed?
- Does the code pull in any dependencies that might have license conflicts
  with this project's license?

**Code**

- Are imports alphabetical and sectioned off by stdlib, 3rdparty, and local?
- Are functions / methods organized alphabetically?
  (or categorized alphabetically)
- Does the change need unit tests?
  (Yes, it probably does!)
- Does the change need documentation?
- Does every function added have function docs?
  (javadoc, pydoc, whatever the language code docs is)
- Does it pass linting?
- Does the code cause backwards compatability breakage?
  (If so it needs documentation)

Google posted an interesting blog on effective code review and how to spend both
your own and your reviewers' time effectively.

.. noqa
https://testing.googleblog.com/2017/06/code-health-too-many-comments-on-your.html


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

JJB YAML Layout
---------------

.. note::

    While some of this applies to the Global JJB project other recommendations
    are generally useful to projects that might be defining JJB templates.

The Global JJB project is a useful example project to look at so we recommend
referring to the Maven job definitions as an example as you read the
documentation below:

https://github.com/lfit/releng-global-jjb/blob/master/jjb/lf-maven-jobs.yaml

In a single YAML file representing a template category for example "Maven"
jobs. We recommend sectioning off the template into 3 general sections in
order:

1. Job Groups (optional)
2. Common Functions
3. Job Template Definitions

In section 1) not all configurations need this so is an optional section. Job
groups are useful in cases where there are jobs that are generally useful
together. For example the OpenDaylight uses a lot of Merge and Verify job
combinations so every new project will want both job types defined in their
project.

In section 2) we want to define all common functions (anchors, aliases, macros)
that are generally useful to all jobs in the file. This allows job template
developers to look at the top of the file to see if there are useful functions
already defined that they can reuse.

In section 3) we can declare our job definitions. In the Global JJB project we
create Gerrit and GitHub versions of the jobs so the format we use here
might look strange at first but is well layed out for code reuse if we need to
define 2 or more versions of the same job template for different systems. We
will define this in more detail in the next section.

Job Template Layout
^^^^^^^^^^^^^^^^^^^

1. Comment of Job Template Name
2. Macro containing build definition of the job
   a. Macro named after job
   b. Complete documentation of the job parameters
   c. Default parameters defined by the job
   d. Job configuration
3. job-template definition containing build triggers

In section 1) we need to declare a in large comment text to identify the job
section.

In section 2) we declare the actual job definition. This is so that we have a
single macro that we call in all the real job-template sections that is
reusable and not duplicating any code. First we declare the macro as the job
name. Then in 2.b) we provide the complete documentation of the job parameters
this is so that we can link users of the job to this file and they can
understand fully what options they can configure for this particular job.
Then we define defaults for any parameters that are optional. The last section
we define the job configuration which completes the macro.

In section 3) we declare the actual job-template. Because of all the
preparations above job template definitions should be small and simple. It
needs to define the scm and job triggers. The Global JJB project needs to
support both Gerrit and GitHub versions of the same job so the job definitions
there have 2 templates for each job defined.


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

JJB has an option to preserve a data structure object when you want to pass
it to a template.
https://docs.openstack.org/infra/jenkins-job-builder/definition.html#variable-references

One thing that is not explicitly covered is the format of the variable name
that you pass the object to. When you use the `{obj:key}` notation to preserve
the original data structure object, it will not work if the variable name has a
dash `-` in it. The standard that we follow, and recommend, is to use an uderscore
`_` instead of a dash.

Example:

.. code-block:: yaml

    - triggers:
       - lf-infra-github-pr-trigger:
           trigger-phrase: '^remerge$'
           status-context: 'JJB Merge'
           permit-all: false
           github-hooks: true
           github-org: '{github-org}'
           github_pr_whitelist: '{obj:github_pr_whitelist}'
           github_pr_admin_list: '{obj:github_pr_admin_list}'

In the above example note the use of underscores in `github_pr_admin_list` and
`github_pr_admin_list`.

from setuptools import find_packages
from setuptools import setup

setup(
    name='lftools',
    version='0.0.3',
    author='Thanh Ha',
    author_email='thanh.ha@linuxfoundation.org',
    url='',
    description='',
    long_description=(
        'The main purpose of Spectrometer is to deliver transparent '
        'statistics of contributions to OpenDaylight Project. It collects '
        'activity data such as 1. commits and number of code lines changed '
        'from ODL Git repositories, 2. reviews from Gerrit, or 3. activities '
        'related to each project from mailing lists and presents the '
        'statistics in a user-friendly manner.'),
    license='EPL',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
    ],
    packages=find_packages(exclude=[
        '*.tests',
        '*.tests.*',
        'tests.*',
        'tests'
    ]),
    entry_points='''
        [console_scripts]
        lftools=lftools.cli:cli
    ''',
    scripts=[
        'shell/patch-odl-release',
        'shell/version',
    ],
)

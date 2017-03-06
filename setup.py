from setuptools import find_packages
from setuptools import setup

from lftools import __version__

with open('requirements.txt') as f:
    install_reqs = f.read().splitlines()

setup(
    name='lftools',
    version=__version__,
    author='Thanh Ha',
    author_email='thanh.ha@linuxfoundation.org',
    url='',
    description='',
    long_description=(
        'LF Tools is a collection of scripts and utilities that are useful '
        'to multiple Linux Foundation project CI and Releng related '
        'activities. We try to create these tools to be generic as possible '
        'such that they can be deployed in other environments.'),
    license='EPL',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=install_reqs,
    packages=find_packages(exclude=[
        '*.tests',
        '*.tests.*',
        'tests.*',
        'tests'
    ]),
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    entry_points='''
        [console_scripts]
        lftools=lftools.cli:main
    ''',
    scripts=[
        'shell/deploy',
        'shell/version',
    ],
)

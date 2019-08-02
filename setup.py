"""Easy and dynamic machine creation."""
import os
from setuptools import find_packages, setup


# load the version
exec(open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'drifter/version.py')).read())

setup(
    name='drifter',
    version=__version__,
    description='Easy and dynamic machine creation.',
    url='https://github.com/bizurkur/drifter',
    license='MIT',
    author=__author__,
    author_email='bizurkur@gmail.com',

    packages=find_packages(exclude=['tests']),
    include_package_data=True,

    install_requires=[
        'click', # core cli functions
        'defusedxml', # safer xml parser
        'PyYAML', # yaml parser
        'six', # 2 to 3 support
        'watchdog', # watch filesystem events (for rsync-auto)
    ],

    entry_points='''
        [console_scripts]
        drifter=drifter.cli:main
        [drifter.providers]
        virtualbox=drifter.providers.virtualbox:virtualbox
    '''
)

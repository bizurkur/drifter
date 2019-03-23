"""
Easy and dynamic machine creation.
"""
from setuptools import find_packages, setup

setup(
    name='drifter',
    version='0.0.1',
    description='Easy and dynamic machine creation.',
    url='https://github.com/bizurkur/drifter',
    license='MIT',
    author='Luke Kingsley',
    author_email='bizurkur@gmail.com',

    packages=find_packages(exclude=['tests']),
    include_package_data=True,

    install_requires=[
        'click', # core cli functions
        'defusedxml', # safer xml parser
        'PyYAML', # yaml parser
        'watchdog', # watch filesystem events (for rsync-auto)
    ],

    entry_points='''
        [console_scripts]
        drifter=drifter.cli:main
    '''
)

from setuptools import setup

setup(
    name='test_provider',
    version='0.1',
    packages=['test_provider'],
    install_requires=[
        'click',
    ],
    entry_points='''
        [drifter.providers]
        my-provider=test_provider:my_provider
    ''',
)

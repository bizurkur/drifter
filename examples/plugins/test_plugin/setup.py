from setuptools import setup

setup(
    name='test_plugin',
    version='0.1',
    packages=['test_plugin'],
    install_requires=[
        'click',
    ],
    entry_points='''
        [drifter.plugins]
        foo=test_plugin:foo
        bar=test_plugin:bar
    ''',
)

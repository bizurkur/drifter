"""Example plugin that does nothing."""
import click

@click.command()
def foo():
    """This is foo"""
    print('You called foo')

@click.command()
def bar():
    """This is bar"""
    print('You called bar')

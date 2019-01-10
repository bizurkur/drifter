from __future__ import print_function, absolute_import, division
import logging
import os

import click

from drifter.commands import CommandLoader
from drifter.config import Config
from drifter.exceptions import DrifterException

__version__ = '0.0.1'
__author__ = 'Luke Kingsley'

def run():
    try:
        main()
    except KeyboardInterrupt as e:
        print()
    except DrifterException as e:
        message = getattr(e, 'msg', e.message)
        click.secho('ERROR: %s' % (message), bold=True, fg='red')

def main():
    config = Config()
    config.load()

    @click.group(invoke_without_command=True, cls=CommandLoader)
    @click.option('--debug', help='Enable debug mode.', is_flag=True)
    @click.version_option(version=__version__, prog_name='Drifter', message='%(prog)s %(version)s')
    @click.pass_context
    def cli(ctx, debug):
        ctx.ensure_object(dict)
        ctx.obj['meta'] = {
            'version': __version__,
            'author': __author__
        }
        ctx.obj['config'] = config

        level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(format='%(levelname)s: %(message)s', level=level)

        if ctx.invoked_subcommand:
            return

        with ctx:
            help_ctx = ctx.command.make_context(
                ctx.info_name,
                ['help'],
                help_option_names=ctx.help_option_names
            )
            with help_ctx:
                help_ctx.command.invoke(help_ctx)

    cli(
        obj={},
        auto_envvar_prefix='DRIFTER',
        help_option_names=['-h', '--help'],
        # TODO: This needs to move to a config
        default_map={
            'up': {
                'name': 'default',
                'provider': 'virtualbox',
            },
            'destroy': {
                'name': 'default',
            },
            'halt': {
                'name': 'default',
            },
            'ssh': {
                'name': 'default',
            },
            'virtualbox': {
                'up': {
                    'name': 'default',
                    'base': '/Users/luke/VirtualBox VMs/ubuntu_bionic64/',
                    'memory': 1024,
                },
                'destroy': {
                    'name': 'default',
                },
                'halt': {
                    'name': 'default',
                },
                'ssh': {
                    'name': 'default',
                },
            }
        }
    )

if __name__ == '__main__':
    run()

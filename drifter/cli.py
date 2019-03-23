"""Drifter."""
from __future__ import absolute_import, division, print_function

import logging
import sys

import click

from drifter.commands import CommandLoader
from drifter.config import Config
from drifter.exceptions import DrifterException

__version__ = '0.1.0'
__author__ = 'Luke Kingsley'


def main():
    """Start running drifter."""
    try:
        run()
    except KeyboardInterrupt as e:
        print()
    except DrifterException as e:
        message = getattr(e, 'msg', e.message)
        logging.error(click.style('ERROR: %s', bold=True, fg='red'), message)
        sys.exit(1)


def run():
    """Run the drifter command."""
    config = Config()
    config.load_state()

    args = sys.argv[1:]
    extra = []
    try:
        pos = args.index('--')
        extra = args[pos + 1:]
        args = args[0:pos]
    except ValueError:
        pass

    @click.group(invoke_without_command=True, cls=CommandLoader)
    @click.version_option(version=__version__, prog_name='Drifter', message='%(prog)s %(version)s')
    @click.pass_context
    def cli(ctx):
        """Create development machines with ease."""
        ctx.ensure_object(dict)
        ctx.obj['meta'] = {
            'version': __version__,
            'author': __author__,
        }
        ctx.obj['config'] = config
        ctx.obj['verbosity'] = 0
        ctx.obj['log_level'] = logging.INFO

        logging.basicConfig(format='%(message)s', level=ctx.obj['log_level'])

        if ctx.invoked_subcommand:
            return

        with ctx:
            help_ctx = ctx.command.make_context(
                ctx.info_name,
                ['help'],
                help_option_names=ctx.help_option_names,
            )
            with help_ctx:
                help_ctx.command.invoke(help_ctx)

    # pylint: disable=unexpected-keyword-arg, no-value-for-parameter
    cli(
        args=args,
        obj={'extra': extra},
        auto_envvar_prefix='DRIFTER',
        help_option_names=['-h', '--help'],
    )


if __name__ == '__main__':
    main()

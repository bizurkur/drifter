"""Drifter."""
from __future__ import absolute_import, division, print_function

import logging
import os
import sys

import click

from drifter.commands import CommandLoader
from drifter.config import Config
from drifter.exceptions import DrifterException


# load the version
# pylint: disable=exec-used
exec(open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'version.py')).read())


def main():
    """Start running drifter."""
    try:
        run()
    except KeyboardInterrupt as e:
        print()
    except DrifterException as e:
        message = str(e)
        logging.error(click.style('ERROR: %s', bold=True, fg='red'), message)
        sys.exit(1)


def run():
    """Run the drifter command."""
    logging.basicConfig(format='%(message)s', level=logging.INFO)
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
    # pylint: disable=undefined-variable
    @click.version_option(version=__version__, prog_name='Drifter', message='%(prog)s %(version)s')  # noqa: F821
    @click.pass_context
    def cli(ctx):
        """Create development machines with ease."""
        ctx.ensure_object(dict)
        ctx.obj['meta'] = {
            # pylint: disable=undefined-variable
            'version': __version__,  # noqa: F821
            # pylint: disable=undefined-variable
            'author': __author__,  # noqa: F821
        }
        ctx.obj['config'] = config
        ctx.obj['verbosity'] = 0
        ctx.obj['log_level'] = logging.INFO

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

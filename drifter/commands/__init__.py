"""Shared command functions."""
from __future__ import absolute_import, division, print_function

import difflib
import os
from functools import update_wrapper

import click

from drifter.providers import get_providers


def _get_name(ctx, unused_param, value):
    if not value:
        return ctx.obj['config'].get_selected()

    return value


NAME_ARGUMENT = click.argument(
    'name',
    metavar='NAME',
    default='',
    callback=_get_name,
)

FORCE_OPTION = click.option(
    '--force',
    '-f',
    help='Do not prompt for confirmation.',
    is_flag=True,
)

QUIET_OPTION = click.option(
    '--quiet',
    '-q',
    help='Do not display output.',
    is_flag=True,
)

PROVIDER_OPTION = click.option(
    '--provider',
    metavar='PROVIDER',
    type=click.Choice(get_providers()),
    help='Which provider to use.',
)

COMMAND_OPTION = click.option(
    '--command',
    '-c',
    metavar='COMMAND',
    help='Command to run after.',
)


def confirm_destroy(name, abort=True):
    """Confirm the user wants to destroy the machine."""
    return click.confirm('Are you sure you want to destroy the "{0}" machine?'.format(name), abort=abort)


def pass_config(func):
    """Pass the config object to the command."""
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        """Invoke the function, adding the config argument."""
        return ctx.invoke(func, ctx.obj['config'], *args, **kwargs)

    return update_wrapper(new_func, func)


def get_commands():
    """Get available commands."""
    commands = []
    for filename in os.listdir(os.path.dirname(__file__)):
        if filename.endswith('.py') and not filename.startswith('__'):
            commands.append(filename[:-3].replace('_', '-'))

    commands.sort()

    return commands


class CommandLoader(click.MultiCommand):
    """Load and display available commands."""

    def list_commands(self, ctx):
        """Display available commands."""
        return get_commands() + get_providers()

    def get_command(self, ctx, cmd_name):
        """Get a command to execute."""
        namespace = {}

        cmd = cmd_name.replace('-', '_')

        folder = os.path.dirname(__file__)
        filename = os.path.join(folder, cmd + '.py')
        if not os.path.exists(filename):
            filename = os.path.join(os.path.dirname(folder), 'providers', cmd, '__init__.py')
            if not os.path.exists(filename):
                return None

        with open(filename) as handle:
            code = compile(handle.read(), filename, 'exec')
            # pylint: disable=eval-used
            eval(code, namespace, namespace)

        if cmd in namespace:
            return namespace[cmd]

        cmd = cmd + '_command'
        if cmd in namespace:
            return namespace[cmd]

        return None

    # Based on https://github.com/click-contrib/click-didyoumean
    def resolve_command(self, ctx, args):
        """Resolve a command.

        Suggest possible command misspellings.
        """
        try:
            return super(CommandLoader, self).resolve_command(ctx, args)
        except click.exceptions.UsageError as error:
            error_msg = str(error)
            original_cmd_name = click.utils.make_str(args[0])
            matches = difflib.get_close_matches(original_cmd_name,
                                                self.list_commands(ctx), 5, 0.5)
            if matches:
                error_msg += '\n\nDid you mean one of these?\n    {0}'.format('\n    '.join(matches))

            raise click.exceptions.UsageError(error_msg, error.ctx)

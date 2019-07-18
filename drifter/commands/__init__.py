"""Shared command functions."""
from __future__ import absolute_import, division, print_function

import difflib
import logging
import os
import sys
from functools import update_wrapper

import click

from pkg_resources import iter_entry_points

from drifter.providers import get_providers


def no_machine_warning():
    """Warn that no machines exist and die."""
    logging.warning(
        click.style(
            'No machines available. Run `drifter up` to create one.',
            bold=True,
            fg='yellow',
        ),
    )
    sys.exit(1)


def list_machines(config, provider=None):
    """List available machines and die if none found."""
    machines = config.list_machines(provider)
    if machines:
        return machines

    return no_machine_warning()


def name_argument(func):
    """Add a machine name argument."""
    def _callback(ctx, unused_param, value):
        if not value:
            return ctx.obj['config'].get_selected()
        return value

    return click.argument('name', metavar='NAME', default='', callback=_callback)(func)


def verbosity_options(func):
    """Add verbosity and quiet options."""
    func = quiet_option(func)
    func = verbosity_option(func)
    return func


def verbosity_option(func):
    """Add a verbosity option."""
    def _callback(ctx, unused_param, value):
        _set_verbosity(ctx, value)
        return value

    return click.option('-v', '--verbose', count=True,
                        expose_value=False, help='Increases verbosity.',
                        callback=_callback)(func)


def quiet_option(func):
    """Add a quiet option."""
    def _callback(ctx, unused_param, value):
        _set_verbosity(ctx, -value)
        return value

    return click.option('-q', '--quiet', count=True,
                        expose_value=False, help='Decreases verbosity.',
                        callback=_callback)(func)


def _set_verbosity(ctx, value):
    ctx.ensure_object(dict)
    ctx.obj['verbosity'] += value
    level = 20 - (ctx.obj['verbosity'] * 10)
    ctx.obj['log_level'] = level
    logging.getLogger().setLevel(level)


def force_option(func):
    """Add a force option."""
    return click.option('-f', '--force', help='Do not prompt for confirmation.', is_flag=True)(func)


def provision_option(func):
    """Add a provision option."""
    return click.option('--provision/--no-provision',
                        help='Whether or not to provision the machine.',
                        is_flag=True, default=None)(func)


def provider_option(func):
    """Add a provider option."""
    return click.option('--provider', metavar='PROVIDER', help='Which provider to use.',
                        type=click.Choice(get_providers()),
                        default=os.environ.get('DRIFTER_PROVIDER'))(func)


def command_option(func):
    """Add a command option."""
    return click.option('-c', '--command', metavar='COMMAND',
                        help='Command to run remotely after operation is complete.')(func)


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


def get_plugins():
    """Get available plugins."""
    plugins = {}
    for entry_point in iter_entry_points('drifter.plugins'):
        plugins[entry_point.name] = entry_point

    return plugins


class CommandLoader(click.MultiCommand):
    """Load and display available commands."""

    def list_commands(self, ctx):
        """Display available commands."""
        return sorted(get_commands() + get_providers() + get_plugins().keys())

    def get_command(self, ctx, cmd_name):
        """Get a command to execute."""
        namespace = {}

        cmd = cmd_name.replace('-', '_')

        # default to commands/
        folder = os.path.dirname(__file__)
        filename = os.path.join(folder, cmd + '.py')
        if not os.path.exists(filename):
            # check for providers/
            filename = os.path.join(os.path.dirname(folder), 'providers', cmd, '__init__.py')
            if not os.path.exists(filename):
                # check for plugins
                plugins = get_plugins()
                if cmd in plugins:
                    return plugins[cmd].load()
                if cmd_name in plugins:
                    return plugins[cmd_name].load()

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
                                                self.list_commands(ctx), 5, 0.6)

            if len(matches) == 1:
                error_msg += '\n\nDid you mean "{0}"?\n'.format(matches[0])
            elif matches:
                error_msg += '\n\nDid you mean one of these?\n    {0}'.format('\n    '.join(matches))

            raise click.exceptions.UsageError(error_msg, error.ctx)

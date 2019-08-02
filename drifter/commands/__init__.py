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
                        type=click.Choice(get_providers().keys()),
                        default=os.environ.get('DRIFTER_PROVIDER'))(func)


def command_option(func):
    """Add a command option."""
    return click.option('-c', '--command', metavar='COMMAND',
                        help='Command to run remotely after operation is complete.')(func)


def run_once_option(func):
    """Add a run once option."""
    return click.option('--run-once', help='Run command only once.', is_flag=True)(func)


def burst_limit_option(func):
    """Add a burst limit option."""
    return click.option('--burst-limit', help='Number of simultaneous file changes to allow.',
                        default=0, type=click.INT)(func)


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
        return sorted(get_commands() + get_providers().keys() + get_plugins().keys())

    def get_command(self, ctx, cmd_name):
        """Get a command to execute."""
        cmd = cmd_name.replace('-', '_')

        command = self._get_command(cmd)
        if not command:
            command = self._get_provider(cmd, cmd_name)
            if not command:
                command = self._get_plugin(cmd, cmd_name)

        return command

    def _get_command(self, cmd):
        namespace = {}

        folder = os.path.dirname(__file__)
        filename = os.path.join(folder, cmd + '.py')
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

    def _get_provider(self, cmd, cmd_name):
        providers = get_providers()
        if cmd in providers:
            return providers[cmd].load()

        if cmd_name in providers:
            return providers[cmd_name].load()

        return None

    def _get_plugin(self, cmd, cmd_name):
        plugins = get_plugins()
        if cmd in plugins:
            return plugins[cmd].load()

        if cmd_name in plugins:
            return plugins[cmd_name].load()

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

    def format_commands(self, ctx, formatter):
        """Format the commands into different output groups."""
        commands = []
        for subcommand in sorted(get_commands() + get_plugins().keys()):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None:
                continue
            if cmd.hidden:
                continue

            commands.append((subcommand, cmd))

        self._format_commands(formatter, 'Commands', commands)

        providers = []
        for subcommand in get_providers():
            cmd = self.get_command(ctx, subcommand)
            if cmd is None:
                continue
            if cmd.hidden:
                continue

            providers.append((subcommand, cmd))

        self._format_commands(formatter, 'Providers', providers)

    def _format_commands(self, formatter, section, commands):
        if not commands:
            return

        limit = formatter.width - 6 - max(len(cmd[0]) for cmd in commands)

        rows = []
        for subcommand, cmd in commands:
            help_text = cmd.get_short_help_str(limit)
            rows.append((subcommand, help_text))

        if rows:
            with formatter.section(section):
                formatter.write_dl(rows)

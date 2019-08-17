"""Open a Secure Shell to a machine."""
from __future__ import absolute_import, division, print_function

import os

import click

import drifter.commands
from drifter.providers import invoke_provider_context
from drifter.utils import get_cli


@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
})
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.command_option
@drifter.commands.pass_config
@click.pass_context
def ssh(ctx, config, name, command):
    """Open a Secure Shell to a machine."""
    name = drifter.commands.validate_name(ctx, name)

    # If there's no command and no name, open SSH to first machine
    if not name and not command:
        machines = drifter.commands.list_machines(config)
        name = machines.pop()

    if name:
        _ssh(ctx, config, name, command)
        return

    # Run an SSH command on all machines
    for machine in drifter.commands.list_machines(config):
        _ssh(ctx, config, machine, command)


def _ssh(ctx, config, name, command):
    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name, '-c', command] + ctx.args)


def do_ssh(config, servers, additional_args=None, command=None, filelist=None, verbose=True):
    """Open an SSH connection to the given server."""
    base_command = ['ssh']
    if additional_args and isinstance(additional_args, list):
        base_command += additional_args

    default_username = config.get_default('ssh.username', 'drifter')

    if not config.get_default('ssh.verify_host_key', False):
        base_command += [
            '-o',
            'StrictHostKeyChecking=no',
            '-o',
            'LogLevel=ERROR',
            '-o',
            'UserKnownHostsFile=/dev/null',
        ]

    private_key = config.get_default('ssh.private_key_path', None)
    if private_key:
        base_command += ['-i', private_key]

    if command:
        responses = []

        if filelist:
            command = command.replace('{}', '"{0}"'.format('" "'.join(filelist)))

        # Run the command on each server
        for server in servers:
            this_command = base_command[:] + [
                '{0}@{1}'.format(
                    server.get('username', default_username),
                    server['ssh_host'],
                ),
                '-p',
                server['ssh_port'],
            ]

            responses.append(get_cli(this_command + [command], verbose))

        return responses

    # Connect to the first server only
    base_command += [
        '{0}@{1}'.format(
            servers[0].get('username', default_username),
            servers[0]['ssh_host'],
        ),
        '-p',
        servers[0]['ssh_port'],
    ]

    return os.execvp('ssh', list(map(str, base_command)))

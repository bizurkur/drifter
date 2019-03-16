from __future__ import print_function, absolute_import, division
import os

import click

import drifter.commands
from drifter.exceptions import GenericException
from drifter.providers import invoke_provider_context
from drifter.utils import get_cli

@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True
})
@drifter.commands.name_argument
@drifter.commands.command_option
@drifter.commands.pass_config
@click.pass_context
def ssh(ctx, config, name, command):
    """Opens a Secure Shell to a machine."""

    if not name:
        machines = config.list_machines()
        if machines:
            name = machines.pop()
        if not name:
            raise GenericException('No machines available.')

    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name, '-c', command] + ctx.args)

def ssh_connect(config, servers, additional_args=[], command=None, filelist=None, verbose=True):
    """Opens an SSH connection to the given server."""

    base_command = ['ssh'] + additional_args

    default_username = config.get_default('ssh.username', 'drifter')

    if not config.get_default('ssh.verify_host_key', False):
        base_command += [
            '-o',
            'StrictHostKeyChecking=no',
            '-o',
            'LogLevel=ERROR',
            '-o',
            'UserKnownHostsFile=/dev/null'
        ]

    private_key = config.get_default('ssh.private_key_path', None)
    if private_key:
        base_command += ['-i', private_key]

    if command:
        responses = []

        if filelist:
            command = command.replace('{}', '"%s"' % ('" "'.join(filelist)))

        # Run the command on each server
        for server in servers:
            this_command = base_command[:] + [
                '%s@%s' % (
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
        '%s@%s' % (
            servers[0].get('username', default_username),
            servers[0]['ssh_host'],
        ),
        '-p',
        servers[0]['ssh_port'],
    ]

    return os.execvp('ssh', map(str, base_command))

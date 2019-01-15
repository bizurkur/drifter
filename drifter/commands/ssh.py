from __future__ import print_function, absolute_import, division
import os

import click

import drifter.commands
from drifter.providers import invoke_provider_context
from drifter.util import get_cli

@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True
})
@drifter.commands.name_argument
@drifter.commands.pass_config
@click.pass_context
def ssh(ctx, config, name):
    """Opens a Secure Shell to a machine."""

    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name] + ctx.args)

def ssh_connect(config, servers, additional_args=[], command=None, filelist=None, verbose=True):
    """Opens an SSH connection to the given server."""

    base_command = ['ssh']

    # TODO: Get this from config
    # if not ssh.get('verify_host_key', False):
    if True:
        base_command += [
            '-o',
            'StrictHostKeyChecking=no',
            '-o',
            'LogLevel=ERROR',
            '-o',
            'UserKnownHostsFile=/dev/null'
        ]

    # TODO: Get this from config
    # private_key = ssh.get('private_key_path', None)
    # if private_key:
    #     base_command += ['-i', private_key]

    base_command += additional_args

    if command:
        responses = []

        if filelist:
            command = command.replace('{}', '"%s"' % ('" "'.join(filelist)))

        # run the command on each server
        for server in servers:
            this_command = base_command[:] + [
                # TODO: Get username from config
                '%s@%s' % (server.get('username', 'drifter'), server['ssh_host']),
                '-p',
                server['ssh_port'],
            ]

            responses.append(get_cli(this_command + [command], verbose))

        return responses

    # connect to the first server only
    base_command += [
        # TODO: Get username from config
        '%s@%s' % (servers[0].get('username', 'drifter'), servers[0]['ssh_host']),
        '-p',
        servers[0]['ssh_port'],
    ]

    return os.execvp('ssh', map(str, base_command))

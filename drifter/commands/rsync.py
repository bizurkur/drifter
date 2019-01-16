from __future__ import print_function, absolute_import, division
import os

import click

import drifter.commands
import drifter.commands.ssh as base_ssh
from drifter.exceptions import GenericException
from drifter.providers import invoke_provider_context
from drifter.util import get_cli

@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True
})
@drifter.commands.name_argument
@drifter.commands.pass_config
@click.pass_context
def rsync(ctx, config, name):
    """Remotely synchronizes files to a machine."""

    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name] + ctx.args)

def rsync_connect(config, servers, additional_args=[],
        command=None, run_auto_command=True, filelist=None, verbose=True):
    """Rsyncs files to the given servers via SSH."""

    local_path = config.get_default('rsync.local', '/')
    remote_path = config.get_default('rsync.remote', None)
    if not remote_path:
        raise GenericException('No remote rsync path specified.')

    local_path = os.path.join(config.base_dir, local_path.strip(os.sep), '')
    remote_path = os.path.join(remote_path, '')

    base_command = _get_base_command(config)
    default_username = config.get_default('ssh.username', 'drifter')

    ssh_params = ''
    if not config.get_default('ssh.verify_host_key', False):
        ssh_params += ' -o StrictHostKeyChecking=no -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null'

    private_key = config.get_default('ssh.private_key_path', None)
    if private_key:
        ssh_params += ' -i "%s"' % (private_key)

    for server in servers:
        this_command = base_command[:] + additional_args + [
            '-e',
            'ssh -p %s%s' % (server['ssh_port'], ssh_params),
            local_path,
            '%s@%s:%s' % (
                server.get('username', default_username),
                server['ssh_host'],
                remote_path,
            ),
        ]

        get_cli(this_command, verbose)

    if run_auto_command and command:
        # TODO: This needs "run-once" support
        return base_ssh.ssh_connect(
            config,
            servers,
            command=command,
            filelist=filelist,
            verbose=verbose
        )

def _get_base_command(config):
    """Gets the base rsync command."""

    command = ['rsync', '--rsync-path', 'sudo rsync']
    command += config.get_default('rsync.args', [
        '--archive',
        '--compress',
        '--delete',
        '--verbose',
        '--no-owner',
        '--no-group',
    ])

    include_list = config.get_default('rsync.include', [])
    for include in include_list:
        command += ['--include', include]

    exclude_list = config.get_default('rsync.exclude', [])
    for exclude in exclude_list:
        command += ['--exclude', exclude]

    return command

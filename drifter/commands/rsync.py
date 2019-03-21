"""Rsync files to a machine."""
from __future__ import absolute_import, division, print_function

import os

import click

import drifter.commands
import drifter.commands.ssh as base_ssh
from drifter.exceptions import GenericException
from drifter.providers import invoke_provider_context
from drifter.utils import get_cli


@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
})
@drifter.commands.NAME_ARGUMENT
@drifter.commands.COMMAND_OPTION
@drifter.commands.QUIET_OPTION
@drifter.commands.pass_config
@click.pass_context
def rsync(ctx, config, name, command, quiet):
    """Rsync files to a machine."""
    # Rsync to the named machine only
    if name:
        _rsync(ctx, config, name, command, quiet)

        return

    machines = config.list_machines()
    if not machines:
        raise GenericException('No machines available.')

    # Rsync to all machines
    for machine in machines:
        _rsync(ctx, config, machine, command, quiet)


def _rsync(ctx, config, name, command, quiet):
    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name, '-c', command] + (['--quiet'] if quiet else []) + ctx.args)


def do_rsync(config, servers, additional_args=None, command=None, filelist=None,
             verbose=True, local_path=None, remote_path=None, **kwargs):
    """Rsync files to the given servers via SSH."""
    local_path = get_local_path(config, local_path)
    if remote_path is None:
        remote_path = get_remote_path(config, remote_path)

    base_command = _get_base_command(config, **kwargs)
    default_username = config.get_default('ssh.username', 'drifter')

    ssh_params = ''
    if not config.get_default('ssh.verify_host_key', False):
        ssh_params += ' -o StrictHostKeyChecking=no -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null'

    private_key = config.get_default('ssh.private_key_path', None)
    if private_key:
        ssh_params += ' -i "{0}"'.format(private_key)

    for server in servers:
        this_command = base_command[:]
        if additional_args and isinstance(additional_args, list):
            this_command += additional_args
        this_command += [
            '-e',
            'ssh -p {0}{1}'.format(server['ssh_port'], ssh_params),
            local_path,
            '{0}@{1}:{2}'.format(
                server.get('username', default_username),
                server['ssh_host'],
                remote_path,
            ),
        ]

        get_cli(this_command, verbose)

    if command:
        base_ssh.do_ssh(config, servers, command=command, filelist=filelist)


def _get_base_command(config, **kwargs):
    command = ['rsync', '--rsync-path', 'sudo rsync']
    rsync_args = kwargs.get('rsync_args', None)
    if rsync_args is None:
        rsync_args = config.get_default('rsync.args', [
            '--archive',
            '--compress',
            '--delete',
            '--verbose',
            '--no-owner',
            '--no-group',
        ])
    command += rsync_args

    include_list = kwargs.get('rsync_include', None)
    if include_list is None:
        include_list = config.get_default('rsync.include', [])
    for include in include_list:
        command += ['--include', include]

    exclude_list = kwargs.get('rsync_exclude', None)
    if exclude_list is None:
        exclude_list = config.get_default('rsync.exclude', [])
    for exclude in exclude_list:
        command += ['--exclude', exclude]

    return command


def get_local_path(config, local_path=None):
    """Get the absolute local path."""
    if not local_path:
        local_path = config.get_default('rsync.local', '/')

    if not local_path.startswith(config.base_dir):
        local_path = os.path.join(config.base_dir, local_path.strip(os.sep), '')

    return os.path.join(local_path, '')


def get_remote_path(config, remote_path=None):
    """Get the remote path."""
    if not remote_path:
        remote_path = config.get_default('rsync.remote', None)
        if not remote_path:
            raise GenericException('No remote rsync path specified.')

    # This assumes local and remote are same OS
    return os.path.join(remote_path, '')

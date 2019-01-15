from __future__ import print_function, absolute_import, division
import os

import click

import drifter.commands
import drifter.commands.ssh as base_ssh
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

def rsync_connect(config, servers, additional_args=[], command=None, run_auto_command=True, filelist=None, verbose=True):
    # TODO: Get paths from config
    local_path = '/'
    remote_path = '/var/www'

    local_path = os.path.join(config.base_dir, local_path.strip(os.sep), '')
    remote_path = os.path.join(remote_path, '')

    base_command = get_base_command()

    ssh_params = ''
    # if not ssh.get('verify_host_key', False):
    if True:
        ssh_params += ' -o StrictHostKeyChecking=no -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null'

    # private_key = ssh.get('private_key_path', None)
    # if private_key:
    #     ssh_params += ' -i "%s"' % (private_key)

    for server in servers:
        this_command = base_command[:] + additional_args + [
            '-e',
            'ssh -p %s%s' % (server['ssh_port'], ssh_params),
            local_path,
            '%s@%s:%s' % (
                # TODO: Get username from config
                server.get('username', 'drifter'),
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

def get_base_command():
    """Gets the base rsync command."""

    default_args = [
        '--archive',
        '--compress',
        '--delete',
        '--verbose',
        '--no-owner',
        '--no-group',
    ]

    command = ['rsync', '--rsync-path', 'sudo rsync']
    # command += settings.get('rsync', {}).get('args', default_args)
    command += default_args

    # include_list = get_include_list(self, settings)
    # for include in include_list:
    #     command += ['--include', include]
    #
    # exclude_list = get_exclude_list(self, settings)
    # for exclude in exclude_list:
    #     command += ['--exclude', exclude]

    # TODO: Remove this.
    command += ['--exclude', '.git/']
    command += ['--exclude', '.tox/']
    command += ['--exclude', '.pytest_cache/']
    command += ['--exclude', 'vendor/']
    command += ['--exclude', 'dist/']
    command += ['--exclude', 'build/']

    return command

# def get_include_list(self, settings):
#     """Gets rsync patterns to include."""
#     return settings.get('rsync', {}).get('include', [])
#
# def get_exclude_list(self, settings):
#     """Gets rsync patterns to exclude."""
#     return settings.get('rsync', {}).get('exclude', [])

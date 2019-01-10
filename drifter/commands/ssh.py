from __future__ import print_function, absolute_import, division
import os

import click

import drifter.commands
from drifter.providers import invoke_provider_context

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

def open_ssh(server, additional_args=[]):

    base_command = ['ssh']
    # if not ssh.get('verify_host_key', False):
    if 1 == 1:
        base_command += [
            '-o',
            'StrictHostKeyChecking=no',
            '-o',
            'LogLevel=ERROR',
            '-o',
            'UserKnownHostsFile=/dev/null'
        ]

    # private_key = ssh.get('private_key_path', None)
    # if private_key:
    #     base_command += ['-i', private_key]

    # if parsed_args.command:
    #     is_verbose = not parsed_args.quiet
    #
    #     command = parsed_args.command
    #     if parsed_args.filename:
    #         command = command.replace('{}', '"%s"' % ('" "'.join(parsed_args.filename)))
    #
    #     command_server_list = []
    #     command_response_list = []
    #
    #     if parsed_args.all:
    #         command_server_list = running_servers
    #     else:
    #         command_server_list = [server]
    #
    #     for command_server in command_server_list:
    #         ssh_command = base_command + pass_thru
    #         ssh_command += [
    #             '%s@%s' % (command_server['username'], command_server['host_ip']),
    #             '-p',
    #             server['port'],
    #             command,
    #         ]
    #
    #         self.trigger_hook('ssh.command.before', parsed_args, args=ssh_command, server=command_server)
    #
    #         res, code = self.get_command_line_response(
    #             ssh_command,
    #             is_verbose
    #         )
    #         command_response_list.append((res, code))
    #
    #         self.trigger_hook('ssh.command.after', parsed_args, args=ssh_command, server=command_server)
    #
    #     return command_response_list

    ssh_args = base_command + additional_args
    ssh_args += ['%s@%s' % (server['username'], server['ssh_host']), '-p', server['ssh_port']]

    # self.trigger_hook('ssh.connect', parsed_args, args=ssh_args, server=server)

    return os.execvp('ssh', map(str, ssh_args))

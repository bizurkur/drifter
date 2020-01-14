"""Provision a machine using a shell script."""
from __future__ import absolute_import, division, print_function

import drifter.commands.ssh as base_ssh
from drifter.exceptions import GenericException


def shell(config, servers, settings, verbose=True):
    """Run the shell script provisioner."""
    if 'path' in settings:
        command = settings['path']
    elif 'inline' in settings:
        command = settings['inline']
    else:
        raise GenericException(
            'Shell provisioners must define a "path" or "inline" command to run.',
        )

    # Build list of environment variables
    exports = ''.join(
        ['export {0}="{1}"; '.format(k, v) for k, v in settings.get('env', {}).items()],
    )
    command = exports + command

    # Run command as privileged user
    sudo = settings.get('sudo', False)
    if sudo:
        # Escape quotes to prevent errors; ' becomes '"'"'
        command = "sudo -- sh -c '{0}'".format(
            command.replace("'", '\'"\'"\''),
        )

    base_ssh.do_ssh(config, servers, command=command, verbose=verbose)

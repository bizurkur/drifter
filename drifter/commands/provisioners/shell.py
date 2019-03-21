"""Provision a machine using a shell script."""
from __future__ import absolute_import, division, print_function

import re

import drifter.commands.ssh as base_ssh
from drifter.exceptions import GenericException


def run(config, servers, provisioner, verbose=True):
    """Run the shell script provisioner."""
    if 'path' in provisioner:
        command = provisioner['path']
    elif 'inline' in provisioner:
        command = provisioner['inline']
    else:
        raise GenericException(
            'Shell provisioners must define a "path" or "inline" command to run.',
        )

    # Build list of environment variables
    exports = ''.join(
        ['export {0}="{1}"; '.format(k, v) for k, v in provisioner.get('env', {}).items()],
    )
    command = exports + command

    # Run command as privileged user
    runas = provisioner.get('runas', None)
    if runas:
        # Escape quotes to prevent errors; ' becomes '"'"'
        command = "sudo runuser -l {0} -c '{1}'".format(
            runas,
            re.sub(r'\'', '\'"\'"\'', command),
        )

    base_ssh.do_ssh(config, servers, command=command, verbose=verbose)

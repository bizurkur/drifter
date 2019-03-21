"""Provision a machine using rsync."""
from __future__ import absolute_import, division, print_function

import drifter.commands.rsync as base_rsync


def run(config, servers, provisioner, verbose=True):
    """Run the rsync provisioner."""
    local_path = provisioner.get('local', None)
    remote_path = provisioner.get('remote', None)
    exclude = provisioner.get('exclude', None)
    include = provisioner.get('include', None)
    args = provisioner.get('args', None)

    base_rsync.do_rsync(config, servers, verbose=verbose,
                        local_path=local_path, remote_path=remote_path,
                        rsync_exclude=exclude, rsync_include=include,
                        rsync_args=args)

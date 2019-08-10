"""Provision a machine using rsync."""
from __future__ import absolute_import, division, print_function

import drifter.commands.rsync as base_rsync


def rsync(config, servers, settings, verbose=True):
    """Run the rsync provisioner."""
    local_path = settings.get('local', None)
    remote_path = settings.get('remote', None)
    exclude = settings.get('exclude', None)
    include = settings.get('include', None)
    args = settings.get('args', None)

    base_rsync.do_rsync(config, servers, verbose=verbose,
                        local_path=local_path, remote_path=remote_path,
                        rsync_exclude=exclude, rsync_include=include,
                        rsync_args=args)

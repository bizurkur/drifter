"""The drifter provisioners package."""
from __future__ import absolute_import, division, print_function

from pkg_resources import iter_entry_points


def get_provisioners():
    """Get a list of available provisioners."""
    provisioners = {}
    for entry_point in iter_entry_points('drifter.provisioners'):
        provisioners[entry_point.name] = entry_point

    return provisioners

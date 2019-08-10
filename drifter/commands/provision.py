"""Provision a machine."""
from __future__ import absolute_import, division, print_function

import logging

import click

import drifter.commands
from drifter.exceptions import GenericException
from drifter.providers import invoke_provider_context
from drifter.provisioners import get_provisioners


@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
})
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.pass_config
@click.pass_context
def provision(ctx, config, name):
    """Provision a machine."""
    # Provision the named machine only
    if name:
        _provision(ctx, config, name)
        return

    # Provision all machines
    for machine in drifter.commands.list_machines(config):
        _provision(ctx, config, machine)


def _provision(ctx, config, name):
    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name] + ctx.args)


def do_provision(config, servers, provisioners=None, verbose=True):
    """Provision the given servers."""
    if provisioners is None:
        provisioners = config.get_default('provision', [])
    if not provisioners:
        return

    privisioner_map = get_provisioners()

    for server in servers:
        for provisioner in provisioners:
            kind = provisioner.get('type', None)
            name = provisioner.get('name', kind)

            if kind not in privisioner_map:
                raise GenericException(
                    'Provisioner of type "{0}" is unknown.'.format(kind),
                )

            if name:
                logging.info('==> Running "%s" provisioner...', name)

            privisioner_map[kind].load()(config, [server], provisioner, verbose)

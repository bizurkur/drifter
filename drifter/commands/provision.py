"""Provision a machine."""
from __future__ import absolute_import, division, print_function

import logging

import click

import drifter.commands
import drifter.commands.provisioners
from drifter.exceptions import GenericException
from drifter.providers import invoke_provider_context


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

    for server in servers:
        for provisioner in provisioners:
            kind = provisioner.get('type', None)
            name = provisioner.get('name', kind)

            if name:
                logging.info('==> Running "%s" provisioner...', name)

            try:
                module = __import__(
                    'drifter.commands.provisioners.{0}'.format(kind),
                    fromlist=['drifter.commands.provisioners'],
                )
            except ImportError:
                raise GenericException(
                    'Provisioner of type "{0}" is unknown.'.format(kind),
                )

            if not getattr(module, 'run', None):
                raise GenericException(
                    'Provisioner of type "{0}" does not define a run command.'.format(name),
                )

            module.run(config, [server], provisioner, verbose)

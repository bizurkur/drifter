"""Provision a machine."""
from __future__ import absolute_import, division, print_function

import click

import drifter.commands
import drifter.commands.provisioners
from drifter.exceptions import GenericException
from drifter.providers import invoke_provider_context


@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
})
@drifter.commands.NAME_ARGUMENT
@drifter.commands.QUIET_OPTION
@drifter.commands.pass_config
@click.pass_context
def provision(ctx, config, name, quiet):
    """Provision a machine."""
    # Provision the named machine only
    if name:
        _provision(ctx, config, name, quiet)

        return

    machines = config.list_machines()
    if not machines:
        raise GenericException('No machines available.')

    # Provision all machines
    for machine in machines:
        _provision(ctx, config, machine, quiet)


def _provision(ctx, config, name, quiet):
    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name] + (['--quiet'] if quiet else []) + ctx.args)


def do_provision(config, servers, provisioners=None, verbose=True):
    """Provision the given servers."""
    if provisioners is None:
        provisioners = config.get_default('provision', [])

    for server in servers:
        for provisioner in provisioners:
            kind = provisioner.get('type', None)
            name = provisioner.get('name', kind)

            if verbose and name:
                click.secho('==> Running "{0}" provisioner...'.format(name))

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

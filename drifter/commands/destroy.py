"""Destroy a machine."""
from __future__ import absolute_import, division, print_function

import click

import drifter.commands
from drifter.exceptions import GenericException
from drifter.providers import invoke_provider_context


@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
})
@drifter.commands.NAME_ARGUMENT
@drifter.commands.FORCE_OPTION
@drifter.commands.QUIET_OPTION
@drifter.commands.pass_config
@click.pass_context
def destroy(ctx, config, name, force, quiet):
    """Destroy a machine."""
    # Destroy the named machine only
    if name:
        _destroy(ctx, config, name, force, quiet)

        return

    machines = config.list_machines()
    if not machines:
        raise GenericException('No machines available.')

    # Destroy all machines
    for machine in machines:
        _destroy(ctx, config, machine, force, quiet)


def _destroy(ctx, config, name, force, quiet):
    if not force and not drifter.commands.confirm_destroy(name, False):
        return

    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name] + ['--force'] + (['--quiet'] if quiet else []) + ctx.args)

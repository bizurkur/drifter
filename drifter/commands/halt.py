"""Halt a machine."""
from __future__ import absolute_import, division, print_function

import click

import drifter.commands
from drifter.providers import invoke_provider_context


@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
})
@drifter.commands.NAME_ARGUMENT
@drifter.commands.QUIET_OPTION
@drifter.commands.pass_config
@click.pass_context
def halt(ctx, config, name, quiet):
    """Halt a machine."""
    # Halt the named machine only
    if name:
        _halt(ctx, config, name, quiet)
        return

    # Halt all machines
    for machine in drifter.commands.list_machines(config):
        _halt(ctx, config, machine, quiet)


def _halt(ctx, config, name, quiet):
    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name] + (['--quiet'] if quiet else []) + ctx.args)

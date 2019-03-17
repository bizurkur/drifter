"""Halt a machine."""
from __future__ import absolute_import, division, print_function

import click

import drifter.commands
from drifter.exceptions import GenericException
from drifter.providers import invoke_provider_context


@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
})
@drifter.commands.name_argument
@drifter.commands.pass_config
@click.pass_context
def halt(ctx, config, name):
    """Halt a machine."""
    # Halt the named machine only
    if name:
        _halt(ctx, config, name)

        return

    machines = config.list_machines()
    if not machines:
        raise GenericException('No machines available.')

    # Halt all machines
    for machine in machines:
        _halt(ctx, config, machine)


def _halt(ctx, config, name):
    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name] + ctx.args)

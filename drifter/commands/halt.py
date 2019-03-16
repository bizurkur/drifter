from __future__ import print_function, absolute_import, division

import click

import drifter.commands
from drifter.exceptions import GenericException
from drifter.providers import invoke_provider_context

@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True
})
@drifter.commands.name_argument
@drifter.commands.pass_config
@click.pass_context
def halt(ctx, config, name):
    """Halts a machine."""

    # Halt the named machine only
    if name:
        halt_machine(ctx, config, name)

        return

    machines = config.list_machines()
    if not machines:
        raise GenericException('No machines available.')

    # Halt all machines
    for machine in machines:
        halt_machine(ctx, config, machine)

def halt_machine(ctx, config, name):
    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name] + ctx.args)

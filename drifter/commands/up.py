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
@drifter.commands.provider_option
@drifter.commands.pass_config
@click.pass_context
def up(ctx, config, name, provider):
    """Brings up a machine or machines."""

    # Start the named machine only
    if name:
        start_machine(ctx, config, name, provider)

        return

    # Check for multi-machine setup
    machines = config.get_default('machines', [])
    if not machines:
        # Check for single machine setup
        name = config.get_default('name')
        if not name:
            raise GenericException('No machines to start up.')
        machines = [name]

    for machine in machines:
        start_machine(ctx, config, machine, provider)

def start_machine(ctx, config, name, provider):
    # Precedence: machine-specific, CLI override, config default, 'virtualbox'
    machine_provider = config.get_default('machines.%s.provider' % (name), provider)
    if not machine_provider:
        machine_provider = config.get_default('provider', 'virtualbox')

    # If no provider given, use the detected one
    if not provider:
        provider = machine_provider

    if config.has_machine(name):
        current_provider = config.get_machine(name).get('provider', '')
        if current_provider != provider:
            raise GenericException(
                'Machine name "%s" is already in use by the "%s" provider.' % (
                    name,
                    current_provider
                )
            )

    invoke_provider_context(ctx, machine_provider, [name] + ctx.args)

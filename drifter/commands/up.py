"""Bring up a machine."""
from __future__ import absolute_import, division, print_function

import click

import drifter.commands
from drifter.exceptions import GenericException
from drifter.providers import invoke_provider_context


@click.command(name='up', context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
})
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.provider_option
@drifter.commands.provision_option
@drifter.commands.pass_config
@click.pass_context
def up_command(ctx, config, name, provider, provision):
    """Bring up a machine."""
    # Start the named machine only
    if name:
        _up_command(ctx, config, name, provider, provision)
        return

    # Check for multi-machine setup
    machines = config.get_default('machines', [])
    if not machines:
        # Check for single machine setup
        name = config.get_default('name')
        if not name:
            drifter.commands.no_machine_warning()
        machines = [name]

    # Add machines from state file
    for machine in config.list_machines():
        if machine not in machines:
            machines.append(machine)

    for machine in machines:
        if not config.get_machine_default(machine, 'autostart', True):
            continue
        _up_command(ctx, config, machine, provider, provision)


def _up_command(ctx, config, name, provider, provision):
    # Precedence: machine-specific, CLI override, config default, 'virtualbox'
    machine_provider = config.get_default('machines.{0}.provider'.format(name), provider)
    if not machine_provider:
        machine_provider = config.get_default('provider', 'virtualbox')

    # If no provider given, use the detected one
    if not provider:
        provider = machine_provider

    if config.has_machine(name):
        current_provider = config.get_machine(name).get('provider', '')
        if current_provider != provider:
            raise GenericException(
                'Machine name "{0}" is already in use by the "{1}" provider.'.format(
                    name,
                    current_provider,
                ),
            )

    args = []
    if provision is True:
        args.append('--provision')
    elif provision is False:
        args.append('--no-provision')

    invoke_provider_context(ctx, machine_provider, [name] + args + ctx.args)

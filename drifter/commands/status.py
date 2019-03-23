"""Get the status of a machine."""
from __future__ import absolute_import, division, print_function

import click

import drifter.commands
from drifter.providers import invoke_provider_context


@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
})
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.pass_config
@click.pass_context
def status(ctx, config, name):
    """Get the status of a machine."""
    # Get the status of the named machine only
    if name:
        _status(ctx, config, name)
        return

    # Get the status of all machines
    for machine in drifter.commands.list_machines(config):
        _status(ctx, config, machine)


def _status(ctx, config, name):
    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name] + ctx.args)

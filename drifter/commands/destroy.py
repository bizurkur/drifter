"""Destroy a machine."""
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
@drifter.commands.force_option
@drifter.commands.pass_config
@click.pass_context
def destroy(ctx, config, name, force):
    """Destroy a machine."""
    # Destroy the named machine only
    if name:
        _destroy(ctx, config, name, force)
        return

    # Destroy all machines
    for machine in drifter.commands.list_machines(config):
        _destroy(ctx, config, machine, force)


def _destroy(ctx, config, name, force):
    if not force and not drifter.commands.confirm_destroy(name, False):
        return

    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name] + ['--force'] + ctx.args)

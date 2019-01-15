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
    """Brings up a machine."""

    if config.has_machine(name):
        current_provider = config.get_machine(name).get('provider', '')
        if current_provider != provider:
            raise GenericException(
                'Machine name "%s" is already in use by the "%s" provider.' % (
                    name,
                    current_provider
                )
            )

    invoke_provider_context(ctx, provider, [name] + ctx.args)

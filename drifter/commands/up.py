from __future__ import print_function, absolute_import, division

import click

import drifter.commands
from drifter.providers import invoke_provider_context

@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True
})
@drifter.commands.name_argument
@drifter.commands.provider_option
@click.pass_context
def up(ctx, name, provider):
    """Brings up a machine."""

    invoke_provider_context(ctx, provider, [name] + ctx.args)

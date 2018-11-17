from __future__ import print_function, absolute_import, division
import os
import click
import commands
import providers

@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True
})
@commands.name_argument
@commands.provider_option
@click.pass_context
def up(ctx, name, provider):
    """Brings up a machine."""

    providers.invoke_provider_context(ctx, provider, [name] + ctx.args)

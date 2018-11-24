from __future__ import print_function, absolute_import, division
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
def rsync_auto(ctx, name, provider):
    """Continously remote synchronizes files to a machine."""

    providers.invoke_provider_context(ctx, provider, [name] + ctx.args)

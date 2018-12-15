from __future__ import print_function, absolute_import, division

import click

import drifter.commands
from drifter.providers import invoke_provider_context

@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True
})
@drifter.commands.name_argument
@drifter.commands.pass_config
@click.pass_context
def rsync_back(ctx, config, name):
    """Remotely synchronizes files from a machine."""

    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name] + ctx.args)

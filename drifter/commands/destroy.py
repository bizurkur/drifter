from __future__ import print_function, absolute_import, division

import click

import drifter.commands
from drifter.providers import invoke_provider_context

@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True
})
@drifter.commands.name_argument
@drifter.commands.force_option
@drifter.commands.pass_config
@click.pass_context
def destroy(ctx, config, name, force):
    """Destroys a machine."""

    provider = config.get_provider(name)

    if not force:
        force = drifter.commands.confirm_destroy(name)

    invoke_provider_context(ctx, provider,
        [name] + (['--force'] if force else []) + ctx.args)

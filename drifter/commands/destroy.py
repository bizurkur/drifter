from __future__ import print_function, absolute_import, division
import click
import commands
import providers

@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True
})
@commands.name_argument
@commands.force_option
@commands.pass_config
@click.pass_context
def destroy(ctx, config, name, force):
    """Destroys a machine."""

    provider = config.get_provider(name)

    if not force:
        commands.confirm_destroy(name)

    providers.invoke_provider_context(ctx, provider,
        [name] + (['--force'] if force else []) + ctx.args)

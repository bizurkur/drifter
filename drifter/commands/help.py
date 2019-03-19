"""Show available commands."""
from __future__ import absolute_import, division, print_function

import click


@click.command(name='help', context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
}, add_help_option=False)
@click.pass_context
def help_command(ctx):
    """Show available commands."""
    click.echo(r"""
     __________________________________________________________
    /  ________________________/  ___________________________  \
   /  /  _____/  /____  /__/__/  /_____/  /________  _____   \  \
  /  /  /  __   /  ___\/  /__   ___/__   ___/  __  \/  ___\  /  /
 /  /  /  /_/  /  /   /  /  /  /     /  /_ /  /___ /  /     /  /
/  /   \______/\_/    \_/  /  /      \___/ \______/\_/     /  /
\  \______________________/  /____________________________/  /
 \__________________________/_______________________________/

Drifter {0} by {1}
""".format(ctx.obj['meta']['version'], ctx.obj['meta']['author']))
    click.echo(ctx.parent.get_help())
    click.echo('')

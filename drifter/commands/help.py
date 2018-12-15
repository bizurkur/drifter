from __future__ import print_function, absolute_import, division

import click

@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True
}, add_help_option=False)
@click.pass_context
def help(ctx):
    """Shows help."""

    click.echo("""
     __________________________________________________________
    /  ________________________/  ___________________________  \\
   /  /  _____/  /____  /__/__/  /_____/  /________  _____   \  \\
  /  /  /  __   /  ___\/  /__   ___/__   ___/  __  \/  ___\  /  /
 /  /  /  /_/  /  /   /  /  /  /     /  /_ /  /___ /  /     /  /
/  /   \______/\_/    \_/  /  /      \___/ \______/\_/     /  /
\  \______________________/  /____________________________/  /
 \__________________________/_______________________________/

Drifter """+ctx.obj['meta']['version']+""" by """+ctx.obj['meta']['author']+"""
""")
    click.echo(ctx.parent.get_help())

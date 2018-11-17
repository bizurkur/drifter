"""VirtualBox provider."""

from __future__ import print_function, absolute_import, division
import logging
import os
import sys
import click
import vboxapi
from providers.virtualbox.provider import Provider

@click.group(invoke_without_command=True)
@click.pass_context
def virtualbox(ctx):
    """Manages VirtualBox machines."""

    ctx.obj['provider'] = Provider()

@virtualbox.command()
@click.argument('name')
@click.pass_context
def halt(ctx, name):
    """Halts a VirtualBox machine."""

    click.secho('Halting machine "%s"...' % (name), bold=True)

    ctx.obj['provider'].load_machine(name)
    ctx.obj['provider'].stop()

@virtualbox.command()
@click.argument('name')
@click.pass_context
def destroy(ctx, name):
    """Destroys a VirtualBox machine."""

    click.secho('Destroying machine "%s"...' % (name), bold=True)

    ctx.obj['provider'].load_machine(name)
    ctx.obj['provider'].destroy()

    # self.config.remove_stack()
    # self.config.save()

@virtualbox.command()
@click.argument('name')
@click.option('--base', help='Machine to use as the base.')
@click.option('--memory', help='Amount of memory to use.', type=click.INT)
@click.option('--mac', help='MAC address to use.')
@click.option('--ports', help='Ports to forward.')
@click.option('--head/--no-head', help='Whether or not to run the VM with a head.', is_flag=True, default=False, show_default=True)
@click.pass_context
def up(ctx, name, base, memory, head, mac, ports):
    """Brings up a VirtualBox machine."""

    click.secho('Bringing up machine "%s"...' % (name), bold=True)

    # create it if it doesn't exist
    if not ctx.obj['provider'].load_machine(name, True):
        click.secho('==> Importing base machine "%s"...' % (base))
        ctx.obj['provider'].create(name, base, memory)

    ctx.obj['provider'].start(head, mac, ports)

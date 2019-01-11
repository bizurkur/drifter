"""VirtualBox provider."""

from __future__ import print_function, absolute_import, division
import logging
import os
import sys

import click
import vboxapi

import drifter.commands
import drifter.commands.ssh as ssh_base
import drifter.providers
from drifter.providers.virtualbox.provider import Provider, VirtualBoxException

@click.group(invoke_without_command=True)
@click.pass_context
def virtualbox(ctx):
    """Manages VirtualBox machines."""

    ctx.obj['provider'] = Provider()

    if not ctx.invoked_subcommand:
        click.echo(ctx.get_help())

@virtualbox.command()
@drifter.commands.name_argument
@click.option('--base', help='Machine to use as the base.')
@click.option('--memory', help='Amount of memory to use.', type=click.INT)
@click.option('--mac', help='MAC address to use.')
@click.option('--ports', help='Ports to forward.')
@click.option('--head/--no-head', help='Whether or not to run the VM with a head.', is_flag=True, default=None)
@drifter.commands.pass_config
@drifter.providers.pass_provider
def up(provider, config, name, base, memory, head, mac, ports):
    """Brings up a VirtualBox machine."""

    if config.has_machine(name):
        settings = config.get_machine(name)
        if 'virtualbox' != settings.get('provider', None):
            raise VirtualBoxException(
                'The machine "%s" already exists for a different provider.' % (name)
            )

    click.secho('Bringing up machine "%s"...' % (name), bold=True)

    # create it if it doesn't exist
    if not provider.load_machine(name, True):
        click.secho('==> Importing base machine "%s"...' % (base))
        provider.create(name)

        config.add_machine(name, {
            'provider': 'virtualbox',
            'id': provider.machine.id,
            'headless': not head,
            'memory': memory,
            'network': {
                'mac': mac,
                'ports': ports,
            },
        })
        config.save()

        provider.clone_from(base)

    try:
        settings = config.get_machine(name)
    except Exception as e:
        # If the settings aren't found, it's because the machine already existed.
        raise VirtualBoxException('A machine named "%s" already exists.' % (name))

    if head is None:
        head = not settings.get('headless', True)
    if not memory:
        memory = settings.get('memory', None)
    if not mac:
        mac = settings.get('network', {}).get('mac', None)
    if not ports:
        ports = settings.get('network', {}).get('ports', None)

    provider.start(head, memory, mac, ports)

@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.force_option
@drifter.commands.pass_config
@drifter.providers.pass_provider
def destroy(provider, config, name, force):
    """Destroys a VirtualBox machine."""

    config.get_machine(name)

    if not force:
        commands.confirm_destroy(name)

    click.secho('Destroying machine "%s"...' % (name), bold=True)

    provider.load_machine(name)
    provider.destroy()

    config.remove_machine(name)
    config.save()

@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.pass_config
@drifter.providers.pass_provider
def halt(provider, config, name):
    """Halts a VirtualBox machine."""

    config.get_machine(name)

    click.secho('Halting machine "%s"...' % (name), bold=True)

    provider.load_machine(name)
    provider.stop()

@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.pass_config
@drifter.providers.pass_provider
def ssh(provider, config, name):
    """Opens an SSH connection to a VirtualBox machine."""

    config.get_machine(name)

    provider.load_machine(name)
    if not provider.is_running():
        raise VirtualBoxException('Machine is not in a started state.')

    server = provider.get_server_data()

    ssh_base.ssh_connect(server)

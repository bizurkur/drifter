"""VirtualBox provider."""
from __future__ import absolute_import, division, print_function

import os

import click

import drifter.commands
import drifter.commands.rsync as rsync_base
import drifter.commands.rsync_auto as rsync_auto_base
import drifter.commands.ssh as ssh_base
import drifter.providers
from drifter.exceptions import GenericException
from drifter.providers.virtualbox.provider import Provider, VirtualBoxException


@click.group(invoke_without_command=True)
@click.pass_context
def virtualbox(ctx):
    """Manage VirtualBox machines."""
    if 'provider' not in ctx.obj:
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
    """Bring up a VirtualBox machine."""
    # Start the named machine only
    if name:
        _up(provider, config, name, base, memory, head, mac, ports)

        return

    # 1. Find machines defined in state file
    # 2. Find machines defined in config
    # 3. Start them all

    provider_machines = config.list_machines('virtualbox')

    # Check for multi-machine setup
    machines = config.get_default('machines', [])
    if not machines:
        # Check for single machine setup
        name = config.get_default('name')
        if name:
            machines = [name]

    for machine in machines:
        if machine in provider_machines:
            continue
        if 'virtualbox' == config.get_machine_default(machine, 'provider', 'virtualbox'):
            provider_machines.append(machine)

    if not provider_machines:
        raise GenericException('No machines available.')

    for machine in provider_machines:
        _up(provider, config, machine, base, memory, head, mac, ports)


def _up(provider, config, name, base, memory, head, mac, ports):
    base, _head, _memory, _mac, _ports = _resolve_up_args(config, name, base,
                                                          memory, head, mac, ports)

    click.secho('Bringing up machine "{0}"...'.format(name), bold=True)

    # Create it if it doesn't exist
    if not provider.load_machine(name, True):
        click.secho('==> Importing base machine "{0}"...'.format(base))
        metadata = provider.get_base_metadata(base)
        provider.create(name, metadata['os'])

        config.add_machine(name, {
            'provider': 'virtualbox',
            'id': provider.machine.id,
            'headless': not _head,
            'memory': _memory,
            'network': {
                'nat': {
                    'mac': _mac,
                    'ports': _ports,
                },
            },
        })
        config.save_state()

        provider.clone_from(metadata['media'])

    try:
        settings = config.get_machine(name)
    except Exception:
        # If the settings aren't found it's because the machine already existed
        # in VirtualBox, but not as a drifter machine.
        raise VirtualBoxException('A machine named "{0}" already exists.'.format(name))

    # If no CLI overrides, load startup options from saved settings
    if head is None:
        head = not settings.get('headless', _head)
    if not memory:
        memory = settings.get('memory', _memory)
    if not mac:
        mac = settings.get('network', {}).get('nat', {}).get('mac', _mac)
    if not ports:
        ports = settings.get('network', {}).get('nat', {}).get('ports', _ports)

    click.secho('==> Starting machine...')
    provider.start(head, memory, mac, ports)


def _resolve_up_args(config, name, base, head, memory, mac, ports):
    if not base:
        base = config.get_machine_default(name, 'base')
        if not base:
            raise VirtualBoxException(
                'Machine "{0}" does not have a base specified.'.format(name),
            )

    if not os.path.exists(base) or not os.path.isdir(base):
        raise VirtualBoxException(
            'Base directory "{0}" does not exist.'.format(base),
        )

    # Precedence: CLI override, machine-specific default, general default
    _head, _memory, _mac, _ports = head, memory, mac, ports
    if _head is None:
        _head = not config.get_machine_default(name, 'headless', True)
    if not _memory:
        _memory = config.get_machine_default(name, 'memory')
    if not _mac:
        _mac = config.get_machine_default(name, 'network.nat.mac')
    if not _ports:
        _ports = config.get_machine_default(name, 'network.nat.ports')

    return (base, _head, _memory, _mac, _ports)


@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.force_option
@drifter.commands.pass_config
@drifter.providers.pass_provider
def destroy(provider, config, name, force):
    """Destroy a VirtualBox machine."""
    if name:
        _destroy(provider, config, name, force)

        return

    machines = config.list_machines('virtualbox')
    if not machines:
        raise GenericException('No machines available.')

    for machine in machines:
        _destroy(provider, config, machine, force)


def _destroy(provider, config, name, force):
    _require_machine(config, name)

    if not force and not drifter.commands.confirm_destroy(name, False):
        return

    click.secho('Destroying machine "{0}"...'.format(name), bold=True)

    provider.load_machine(name)
    provider.destroy()

    config.remove_machine(name)
    config.save_state()


@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.pass_config
@drifter.providers.pass_provider
def halt(provider, config, name):
    """Halt a VirtualBox machine."""
    if name:
        _halt(provider, config, name)

        return

    machines = config.list_machines('virtualbox')
    if not machines:
        raise GenericException('No machines available.')

    for machine in machines:
        _halt(provider, config, machine)


def _halt(provider, config, name):
    _require_machine(config, name)

    click.secho('Halting machine "{0}"...'.format(name), bold=True)

    provider.load_machine(name)
    # TODO: This should probably try `sudo shutdown now`
    provider.stop()


@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.command_option
@drifter.commands.pass_config
@drifter.providers.pass_provider
@click.pass_context
def ssh(ctx, provider, config, name, command):
    """Open a Secure Shell to a VirtualBox machine."""
    name = _resolve_name(config, name)
    _require_running_machine(config, name, provider)

    server = provider.get_server_data()

    ssh_base.ssh_connect(config, [server], command=command,
                         additional_args=ctx.obj['extra'])


@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.command_option
@drifter.commands.pass_config
@drifter.providers.pass_provider
@click.pass_context
def rsync(ctx, provider, config, name, command):
    """Rsync files to a VirtualBox machine."""
    if name:
        _rsync(ctx, provider, config, name, command)

        return

    machines = config.list_machines('virtualbox')
    if not machines:
        raise GenericException('No machines available.')

    for machine in machines:
        _rsync(ctx, provider, config, machine, command)


def _rsync(ctx, provider, config, name, command):
    _require_running_machine(config, name, provider)

    server = provider.get_server_data()

    click.secho('Rsyncing to machine "{0}"...'.format(name), bold=True)

    rsync_base.rsync_connect(config, [server], command=command,
                             additional_args=ctx.obj['extra'])


@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.command_option
@click.option('--run-once', help='Run command only once.', is_flag=True)
@click.option('--burst-limit', help='Number of simultaneous file changes to allow.', default=0, type=click.INT)
@drifter.commands.pass_config
@drifter.providers.pass_provider
@click.pass_context
def rsync_auto(ctx, provider, config, name, command, run_once, burst_limit):
    """Automatically rsync files to a VirtualBox machine."""
    name = _resolve_name(config, name)
    _require_running_machine(config, name, provider)

    server = provider.get_server_data()

    rsync_auto_base.rsync_auto_connect(config, [server], command=command,
                                       additional_args=ctx.obj['extra'],
                                       run_once=run_once, burst_limit=burst_limit)


def _resolve_name(config, name):
    if not name:
        machines = config.list_machines('virtualbox')
        if machines:
            name = machines.pop()
        if not name:
            raise GenericException('No machines available.')

    return name


def _require_machine(config, name):
    config.get_machine(name)


def _require_running_machine(config, name, provider):
    _require_machine(config, name)

    provider.load_machine(name)
    if not provider.is_running():
        raise VirtualBoxException('Machine is not in a started state.')

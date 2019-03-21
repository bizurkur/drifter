"""VirtualBox provider."""
from __future__ import absolute_import, division, print_function

import os

import click

import drifter.commands
import drifter.commands.provision as provision_base
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


@virtualbox.command(name='up')
@drifter.commands.NAME_ARGUMENT
@drifter.commands.QUIET_OPTION
@click.option('--base', help='Machine to use as the base.')
@click.option('--memory', help='Amount of memory to use.', type=click.INT)
@click.option('--mac', help='MAC address to use.')
@click.option('--ports', help='Ports to forward.')
@click.option('--head/--no-head', help='Whether or not to run the VM with a head.', is_flag=True, default=None)
@drifter.commands.pass_config
@drifter.providers.pass_provider
def up_command(provider, config, name, quiet, base, memory, head, mac, ports):
    """Bring up a VirtualBox machine."""
    # Start the named machine only
    if name:
        _up_command(provider, config, name, quiet, base, memory, head, mac, ports)

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
        if config.get_machine_default(machine, 'provider', 'virtualbox') == 'virtualbox':
            provider_machines.append(machine)

    if not provider_machines:
        raise GenericException('No machines available.')

    for machine in provider_machines:
        _up_command(provider, config, machine, quiet, base, memory, head, mac, ports)


def _up_command(provider, config, name, quiet, base, memory, head, mac, ports):
    base, _head, _memory, _mac, _ports = _resolve_up_args(config, name, base,
                                                          memory, head, mac, ports)

    if not quiet:
        click.secho('Bringing up machine "{0}"...'.format(name), bold=True)

    # Create it if it doesn't exist
    if not provider.load_machine(name, True):
        if not quiet:
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

    if not quiet:
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
@drifter.commands.NAME_ARGUMENT
@drifter.commands.QUIET_OPTION
@drifter.commands.pass_config
@drifter.providers.pass_provider
def provision(provider, config, name, quiet):
    """Provision a VirtualBox machine."""
    if name:
        _provision(provider, config, name, quiet)

        return

    machines = config.list_machines('virtualbox')
    if not machines:
        raise GenericException('No machines available.')

    for machine in machines:
        _provision(provider, config, machine, quiet)


def _provision(provider, config, name, quiet):
    _require_machine(config, name)

    if not quiet:
        click.secho('Provisioning machine "{0}"...'.format(name), bold=True)

    provider.load_machine(name)

    server = provider.get_server_data()
    provisioners = config.get_machine_default(name, 'provision', [])

    provision_base.do_provision(config, [server], provisioners, verbose=not quiet)


@virtualbox.command()
@drifter.commands.NAME_ARGUMENT
@drifter.commands.FORCE_OPTION
@drifter.commands.QUIET_OPTION
@drifter.commands.pass_config
@drifter.providers.pass_provider
def destroy(provider, config, name, force, quiet):
    """Destroy a VirtualBox machine."""
    if name:
        _destroy(provider, config, name, force, quiet)

        return

    machines = config.list_machines('virtualbox')
    if not machines:
        raise GenericException('No machines available.')

    for machine in machines:
        _destroy(provider, config, machine, force, quiet)


def _destroy(provider, config, name, force, quiet):
    _require_machine(config, name)

    if not force and not drifter.commands.confirm_destroy(name, False):
        return

    if not quiet:
        click.secho('Destroying machine "{0}"...'.format(name), bold=True)

    provider.load_machine(name)
    provider.destroy()

    config.remove_machine(name)
    if config.get_selected() == name:
        config.set_selected(None)
    config.save_state()


@virtualbox.command()
@drifter.commands.NAME_ARGUMENT
@drifter.commands.QUIET_OPTION
@drifter.commands.pass_config
@drifter.providers.pass_provider
def halt(provider, config, name, quiet):
    """Halt a VirtualBox machine."""
    if name:
        _halt(provider, config, name, quiet)

        return

    machines = config.list_machines('virtualbox')
    if not machines:
        raise GenericException('No machines available.')

    for machine in machines:
        _halt(provider, config, machine, quiet)


def _halt(provider, config, name, quiet):
    _require_machine(config, name)

    if not quiet:
        click.secho('Halting machine "{0}"...'.format(name), bold=True)

    provider.load_machine(name)
    provider.stop()


@virtualbox.command()
@drifter.commands.NAME_ARGUMENT
@drifter.commands.COMMAND_OPTION
@drifter.commands.QUIET_OPTION
@drifter.commands.pass_config
@drifter.providers.pass_provider
@click.pass_context
def ssh(ctx, provider, config, name, command, quiet):
    """Open a Secure Shell to a VirtualBox machine."""
    name = _resolve_name(config, name)
    _require_running_machine(config, name, provider)

    server = provider.get_server_data()

    ssh_base.do_ssh(config, [server], command=command, verbose=not quiet,
                    additional_args=ctx.obj['extra'])


@virtualbox.command()
@drifter.commands.NAME_ARGUMENT
@drifter.commands.COMMAND_OPTION
@drifter.commands.QUIET_OPTION
@drifter.commands.pass_config
@drifter.providers.pass_provider
@click.pass_context
def rsync(ctx, provider, config, name, command, quiet):
    """Rsync files to a VirtualBox machine."""
    if name:
        _rsync(ctx, provider, config, name, command, quiet)

        return

    machines = config.list_machines('virtualbox')
    if not machines:
        raise GenericException('No machines available.')

    for machine in machines:
        _rsync(ctx, provider, config, machine, command, quiet)


def _rsync(ctx, provider, config, name, command, quiet):
    _require_running_machine(config, name, provider)

    server = provider.get_server_data()

    if not quiet:
        click.secho('Rsyncing to machine "{0}"...'.format(name), bold=True)

    rsync_base.do_rsync(config, [server], command=command, verbose=not quiet,
                        additional_args=ctx.obj['extra'])


@virtualbox.command()
@drifter.commands.NAME_ARGUMENT
@drifter.commands.COMMAND_OPTION
@drifter.commands.QUIET_OPTION
@click.option('--run-once', help='Run command only once.', is_flag=True)
@click.option('--burst-limit', help='Number of simultaneous file changes to allow.', default=0, type=click.INT)
@drifter.commands.pass_config
@drifter.providers.pass_provider
@click.pass_context
def rsync_auto(ctx, provider, config, name, command, quiet, run_once, burst_limit):
    """Automatically rsync files to a VirtualBox machine."""
    name = _resolve_name(config, name)
    _require_running_machine(config, name, provider)

    server = provider.get_server_data()

    rsync_auto_base.rsync_auto_connect(config, [server], command=command,
                                       additional_args=ctx.obj['extra'],
                                       run_once=run_once, burst_limit=burst_limit,
                                       verbose=not quiet)


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

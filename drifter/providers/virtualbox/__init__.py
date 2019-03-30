"""VirtualBox provider."""
from __future__ import absolute_import, division, print_function

import logging
import os
from time import gmtime, sleep, strftime

import click

import drifter.commands
import drifter.commands.provision as base_provision
import drifter.commands.rsync as base_rsync
import drifter.commands.rsync_auto as base_rsync_auto
import drifter.commands.ssh as base_ssh
import drifter.providers
from drifter.exceptions import ProviderException
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
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.provision_option
@click.option('--base', help='Machine to use as the base.', type=click.Path(
    exists=True, file_okay=False, dir_okay=True, writable=False,
    readable=True, resolve_path=True, allow_dash=False))
@click.option('--memory', help='Amount of memory to use.', type=click.INT)
@click.option('--mac', help='MAC address to use.')
@click.option('--ports', help='Ports to forward.')
@click.option('--head/--no-head', help='Whether or not to run the VM with a head.', is_flag=True, default=None)
@drifter.commands.pass_config
@drifter.providers.pass_provider
def up_command(provider, config, name, provision, base, memory, head, mac, ports):
    """Bring up a VirtualBox machine."""
    # Start the named machine only
    if name:
        _up_command(provider, config, name, provision, base, memory, head, mac, ports)
        return

    # 1. Find machines defined in state file
    # 2. Find machines defined in config
    # 3. Start them all

    provider_machines = config.list_machines('virtualbox')

    # Check for multi-machine setup
    machines = config.get_default('machines', {}).keys()
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
        drifter.commands.no_machine_warning()

    for machine in provider_machines:
        if not config.get_machine_default(machine, 'autostart', True):
            continue
        _up_command(provider, config, machine, provision, base, memory, head, mac, ports)


def _up_command(provider, config, name, provision, base, memory, head, mac, ports):
    base, _head, _memory, _mac, _ports = _resolve_up_args(config, name, base,
                                                          memory, head, mac, ports)

    logging.info(click.style('Bringing up machine "%s"...', bold=True), name)

    try:
        _ensure_machine_exists(provider, config, name, base, _head, _memory, _mac, _ports)
    except ProviderException as e:
        _destroy(provider, config, name, True, False)
        raise e

    try:
        settings = config.get_machine(name)
    except Exception:
        # If the settings aren't found it's because the machine already existed
        # in VirtualBox, but not as a drifter machine.
        raise VirtualBoxException('A machine named "{0}" already exists.'.format(name))

    # If no CLI overrides, load startup options from saved settings
    head = head if head is not None else not settings.get('headless', _head)
    memory = memory or settings.get('memory', _memory)
    mac = mac or settings.get('network', {}).get('nat', {}).get('mac', _mac)
    ports = ports or settings.get('network', {}).get('nat', {}).get('ports', _ports)

    logging.info('==> Starting machine...')
    real_name = _get_machine_name(config, name)
    provider.start(real_name, head, memory, mac, ports)

    _do_up_provision(provider, config, name, provision)


def _do_up_provision(provider, config, name, provision):
    """Execute provision, if applicable."""
    # Do not provision
    if provision is False:
        return

    # Already provisioned
    settings = config.get_machine(name)
    if settings.get('provisioned', False) and not provision:
        logging.info('==> Skipping provision because it already ran.')
        logging.info('==> Use the --provision flag to force a provision or run `drifter provision`')
        return

    # Do provision
    real_name = _get_machine_name(config, name)
    server = provider.get_server_data(real_name)
    while True:
        logging.info('==> Checking if SSH connection is alive...')
        res = base_ssh.do_ssh(config, [server], command='cd .', verbose=False)
        if res and res[0][1] == 0:
            break
        sleep(10)

    _provision(provider, config, name)


def _ensure_machine_exists(provider, config, name, base, head, memory, mac, ports):
    """Create a machine, if it doesn't already exist."""
    real_name = _get_machine_name(config, name)
    if provider.load_machine(real_name, True):
        return

    # Create it if it doesn't exist
    logging.info('==> Importing base machine "%s"...', base)

    metadata = provider.get_base_metadata(base)
    data = provider.create(real_name, metadata['os'])

    config.add_machine(name, {
        'name': real_name,
        'provider': 'virtualbox',
        'id': data.get('uuid', None),
        'headless': not head,
        'memory': memory,
        'network': {
            'nat': {
                'mac': mac,
                'ports': ports,
            },
        },
    })
    config.save_state()

    provider.clone_from(real_name, metadata['media'])


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


@virtualbox.command(name='provision')
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.pass_config
@drifter.providers.pass_provider
def provision_command(provider, config, name):
    """Provision a VirtualBox machine."""
    if name:
        _provision(provider, config, name)
        return

    for machine in drifter.commands.list_machines(config, 'virtualbox'):
        _provision(provider, config, machine)


def _provision(provider, config, name):
    _require_machine(config, name)

    logging.info(click.style('Provisioning machine "%s"...', bold=True), name)

    real_name = _get_machine_name(config, name)
    provider.load_machine(real_name)

    server = provider.get_server_data(real_name)
    provisioners = config.get_machine_default(name, 'provision', [])

    base_provision.do_provision(config, [server], provisioners)

    config.get_machine(name)['provisioned'] = True
    config.save_state()


@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.force_option
@drifter.commands.pass_config
@drifter.providers.pass_provider
def destroy(provider, config, name, force):
    """Destroy a VirtualBox machine."""
    if name:
        _destroy(provider, config, name, force)
        return

    for machine in drifter.commands.list_machines(config, 'virtualbox'):
        _destroy(provider, config, machine, force)


def _destroy(provider, config, name, force, require=True):
    if require:
        _require_machine(config, name)
    elif not config.has_machine(name):
        return

    if not force and not drifter.commands.confirm_destroy(name, False):
        return

    logging.info(click.style('Destroying machine "%s"...', bold=True), name)

    real_name = _get_machine_name(config, name)
    if provider.load_machine(real_name, True):
        provider.destroy(real_name)

    config.remove_machine(name)
    if config.get_selected() == name:
        config.set_selected(None)
    config.save_state()


@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.pass_config
@drifter.providers.pass_provider
def halt(provider, config, name):
    """Halt a VirtualBox machine."""
    if name:
        _halt(provider, config, name)
        return

    for machine in drifter.commands.list_machines(config, 'virtualbox'):
        _halt(provider, config, machine)


def _halt(provider, config, name):
    _require_machine(config, name)

    logging.info(click.style('Halting machine "%s"...', bold=True), name)

    real_name = _get_machine_name(config, name)
    provider.load_machine(real_name)
    provider.stop(real_name)


@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.pass_config
@drifter.providers.pass_provider
def status(provider, config, name):
    """Get the status of a VitualBox machine."""
    if name:
        _status(provider, config, name)
        return

    for machine in drifter.commands.list_machines(config, 'virtualbox'):
        _status(provider, config, machine)


def _status(provider, config, name):
    settings = config.get_machine(name)
    real_name = _get_machine_name(config, name)
    provider.load_machine(real_name)

    output = [
        ['Name:', '{0} ({1})'.format(name, settings.get('provider', 'unknown'))],
        ['Status:', 'Running' if provider.is_running(real_name) else 'Halted'],
    ]

    server = provider.get_server_data(real_name)
    for forward in server['redirects']:
        output.append(['Ports:', '{0} (host) -> {1} (guest)'.format(forward['host_port'], forward['guest_port'])])

    click.echo('')

    longest_output_key = max(len(x[0]) for x in output)
    for entry in output:
        click.echo('  {0:{1}}  {2}'.format(entry[0], longest_output_key, entry[1]))

    click.echo('')


@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.command_option
@drifter.commands.pass_config
@drifter.providers.pass_provider
@click.pass_context
def ssh(ctx, provider, config, name, command):
    """Open a Secure Shell to a VirtualBox machine."""
    if not name:
        machines = drifter.commands.list_machines(config, 'virtualbox')
        name = machines.pop()

    _require_running_machine(config, name, provider)

    real_name = _get_machine_name(config, name)
    server = provider.get_server_data(real_name)

    verbose = True
    if ctx.obj['verbosity'] < 0:
        verbose = False

    base_ssh.do_ssh(config, [server], command=command, verbose=verbose,
                    additional_args=ctx.obj['extra'])


@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.command_option
@drifter.commands.pass_config
@drifter.providers.pass_provider
@click.pass_context
def rsync(ctx, provider, config, name, command):
    """Rsync files to a VirtualBox machine."""
    if name:
        _rsync(ctx, provider, config, name, command)
        return

    for machine in drifter.commands.list_machines(config, 'virtualbox'):
        _rsync(ctx, provider, config, machine, command)


def _rsync(ctx, provider, config, name, command):
    _require_running_machine(config, name, provider)

    real_name = _get_machine_name(config, name)
    server = provider.get_server_data(real_name)

    logging.info(click.style('Rsyncing to machine "%s"...', bold=True), name)

    verbose = True
    if ctx.obj['verbosity'] < 0:
        verbose = False

    base_rsync.do_rsync(config, [server], command=command, verbose=verbose,
                        additional_args=ctx.obj['extra'])


@virtualbox.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.command_option
@click.option('--run-once', help='Run command only once.', is_flag=True)
@click.option('--burst-limit', help='Number of simultaneous file changes to allow.', default=0, type=click.INT)
@drifter.commands.pass_config
@drifter.providers.pass_provider
@click.pass_context
def rsync_auto(ctx, provider, config, name, command, run_once, burst_limit):
    """Automatically rsync files to a VirtualBox machine."""
    if not name:
        machines = drifter.commands.list_machines(config, 'virtualbox')
        name = machines.pop()

    _require_running_machine(config, name, provider)

    real_name = _get_machine_name(config, name)
    server = provider.get_server_data(real_name)

    verbose = True
    if ctx.obj['verbosity'] < 0:
        verbose = False

    base_rsync_auto.do_rsync_auto(config, [server], command=command,
                                  additional_args=ctx.obj['extra'],
                                  run_once=run_once, burst_limit=burst_limit,
                                  verbose=verbose)


def _require_machine(config, name):
    config.get_machine(name)


def _require_running_machine(config, name, provider):
    _require_machine(config, name)

    real_name = _get_machine_name(config, name)
    provider.load_machine(real_name)
    if not provider.is_running(real_name):
        raise VirtualBoxException('Machine is not in a started state.')


def _get_machine_name(config, name):
    """Get the real name of the machine."""
    if config.has_machine(name):
        settings = config.get_machine(name)

        return settings.get('name', name)

    project = os.path.basename(config.base_dir.rstrip(os.sep))
    timestamp = strftime('%H%M%S', gmtime())

    return '{0}_{1}_{2}'.format(project, name, timestamp)

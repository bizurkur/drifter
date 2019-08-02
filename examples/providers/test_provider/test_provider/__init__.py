"""Example provider that does nothing.

All the public methods in this example should work for any provider without much
(if any) modification. The protected methods are where the provider-specific
changes need to go.
"""
from __future__ import absolute_import, division, print_function

import logging

import click

import drifter.commands
import drifter.commands.provision as base_provision
import drifter.commands.rsync as base_rsync
import drifter.commands.rsync_auto as base_rsync_auto
import drifter.commands.ssh as base_ssh
import drifter.providers
from drifter.exceptions import ProviderException


PROVIDER_NAME = 'my-provider'


# Making your provider throw unique exceptions makes things easier to trace/catch.
# All exceptions should extend the base ProviderException.
class MyProviderException(ProviderException):
    """Exception to represent a MyProvider error."""

    pass


@click.group(invoke_without_command=True)
@click.pass_context
def my_provider(ctx):
    """Example provider."""
    if not ctx.invoked_subcommand:
        click.echo(ctx.get_help())


@my_provider.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.provision_option
@drifter.commands.pass_config
def up(config, name, provision):
    """Bring up a machine."""
    # Start the named machine only
    if name:
        _up(config, name, provision)
        return

    # 1. Find machines defined in state file
    # 2. Find machines defined in config
    # 3. Start them all

    provider_machines = config.list_machines(PROVIDER_NAME)

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
        if config.get_machine_default(machine, 'provider',
                drifter.providers.DEFAULT_PROVIDER) == PROVIDER_NAME:
            provider_machines.append(machine)

    if not provider_machines:
        drifter.commands.no_machine_warning()

    for machine in provider_machines:
        if not config.get_machine_default(machine, 'autostart', True):
            continue
        _up(config, machine, provision)


@my_provider.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.pass_config
def provision(config, name):
    """Provision a machine."""
    if name:
        _provision(config, name)
        return

    for machine in drifter.commands.list_machines(config, PROVIDER_NAME):
        _provision(config, machine)


@my_provider.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.force_option
@drifter.commands.pass_config
def destroy(config, name, force):
    """Destroy a machine."""
    if name:
        _destroy(config, name, force)
        return

    for machine in drifter.commands.list_machines(config, PROVIDER_NAME):
        _destroy(config, machine, force)


@my_provider.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.pass_config
def halt(config, name):
    """Halt a machine."""
    if name:
        _halt(config, name)
        return

    for machine in drifter.commands.list_machines(config, PROVIDER_NAME):
        _halt(config, machine)


@my_provider.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.pass_config
def status(config, name):
    """Get the status of a machine."""
    if name:
        _status(config, name)
        return

    for machine in drifter.commands.list_machines(config, PROVIDER_NAME):
        _status(config, machine)


@my_provider.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.command_option
@drifter.commands.pass_config
@click.pass_context
def ssh(ctx, config, name, command):
    """Open a Secure Shell to a machine."""
    if not name:
        machines = drifter.commands.list_machines(config, PROVIDER_NAME)
        name = machines.pop()

    _require_running_machine(config, name)

    # Load data about the server.
    server = _get_server_data(name)

    verbose = True
    if ctx.obj['verbosity'] < 0:
        verbose = False

    base_ssh.do_ssh(config, [server], command=command, verbose=verbose,
                    additional_args=ctx.obj['extra'])


@my_provider.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.command_option
@drifter.commands.pass_config
@click.pass_context
def rsync(ctx, config, name, command):
    """Rsync files to a machine."""
    if name:
        _rsync(ctx, config, name, command)
        return

    for machine in drifter.commands.list_machines(config, PROVIDER_NAME):
        _rsync(ctx, config, machine, command)


@my_provider.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.command_option
@drifter.commands.run_once_option
@drifter.commands.burst_limit_option
@drifter.commands.pass_config
@click.pass_context
def rsync_auto(ctx, config, name, command, run_once, burst_limit):
    """Automatically rsync files to a machine."""
    if not name:
        machines = drifter.commands.list_machines(config, PROVIDER_NAME)
        name = machines.pop()

    _require_running_machine(config, name)

    # Load data about the server.
    server = _get_server_data(name)

    verbose = True
    if ctx.obj['verbosity'] < 0:
        verbose = False

    base_rsync_auto.do_rsync_auto(config, [server], command=command,
                                  additional_args=ctx.obj['extra'],
                                  run_once=run_once, burst_limit=burst_limit,
                                  verbose=verbose)


################################################################################
################################################################################
# All of the below protected methods are the bulk of what would need modified to
# be specific to your provider. They could also be moved to an external class.
################################################################################
################################################################################

def _up(config, name, provision):
    logging.info(click.style('Bringing up machine "%s"...', bold=True), name)

    if not config.has_machine(name):
        # Create the machine here.
        # Once the machine exists, add it to the config
        config.add_machine(name, {
            # This is the "internal" name and does NOT have to match the name of the
            # machine given by the user, e.g. machine "testing" might actually point
            # to a VM named "foo_testing_123" to avoid conflicts.
            'name': name,

            # Always specify what provider the machine is for.
            'provider': PROVIDER_NAME,

            # Add any other settings you might need.
            # Ideally, all the settings you need to "up" a machine should be here.
        })
        config.save_state()

    # Do what you need to start the machine here.
    # ...


def _provision(config, name):
    _require_machine(config, name)

    logging.info(click.style('Provisioning machine "%s"...', bold=True), name)

    # Load data about the server.
    server = _get_server_data(name)

    # Get provisioners for the machine.
    provisioners = config.get_machine_default(name, 'provision', [])

    # Do the provision.
    base_provision.do_provision(config, [server], provisioners)

    # Save that a provision was completed.
    config.get_machine(name)['provisioned'] = True
    config.save_state()


def _destroy(config, name, force):
    _require_machine(config, name)

    if not force and not drifter.commands.confirm_destroy(name, False):
        return

    logging.info(click.style('Destroying machine "%s"...', bold=True), name)

    # Destroy the machine here
    # ...

    # Save that it's destroyed.
    config.remove_machine(name)
    if config.get_selected() == name:
        config.set_selected(None)
    config.save_state()


def _halt(config, name):
    _require_machine(config, name)

    logging.info(click.style('Halting machine "%s"...', bold=True), name)

    # Halt your machine
    # ...


def _status(config, name):
    settings = config.get_machine(name)

    output = [
        ['Name:', '{0} ({1})'.format(name, settings.get('provider', 'unknown'))],
        ['Status:', 'Faked'],
    ]

    # Add any additional data, like port redirects.
    # ...

    click.echo('')

    longest_output_key = max(len(x[0]) for x in output)
    for entry in output:
        click.echo('  {0:{1}}  {2}'.format(entry[0], longest_output_key, entry[1]))

    click.echo('')


def _rsync(ctx, config, name, command):
    _require_running_machine(config, name)

    logging.info(click.style('Rsyncing to machine "%s"...', bold=True), name)

    # Load data about the server.
    server = _get_server_data(name)

    verbose = True
    if ctx.obj['verbosity'] < 0:
        verbose = False

    base_rsync.do_rsync(config, [server], command=command, verbose=verbose,
                        additional_args=ctx.obj['extra'])


def _get_server_data(name):
    # Load data about the server.
    # Get this data from wherever you need to.
    # As an example, this is a static dict.
    # ssh_port and ssh_host are required, additional data is optional.
    return {
        'ssh_port': 22,
        'ssh_host': 'drifter.example.local', # This should be an IP, ideally
    }


def _require_machine(config, name):
    # This will throw an exception if the machine isn't found.
    config.get_machine(name)


def _require_running_machine(config, name):
    _require_machine(config, name)

    # Do whatever checks are needed to see if machine is running.
    running = True

    if not running:
        raise MyProviderException('Machine is not in a started state.')

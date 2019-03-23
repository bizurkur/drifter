"""List available machines."""
from __future__ import absolute_import, division, print_function

import click

import drifter.commands
from drifter.exceptions import InvalidArgumentException


@click.command(name='list')
@drifter.commands.verbosity_options
@click.option('--select', help='Selects a machine')
@click.option('--no-select', help='Selects no machines', is_flag=True)
@drifter.commands.pass_config
def list_command(config, select, no_select):
    """List available machines."""
    machines = drifter.commands.list_machines(config)
    machines.sort()

    if select:
        _select(config, select, machines)
    elif no_select:
        config.set_selected(None)
        config.save_state()

    click.echo('')

    selected = config.get_selected()
    for i in xrange(len(machines)):
        name = machines[i]
        provider = config.get_machine(machines[i]).get('provider', 'unknown')
        if name == selected:
            click.secho('  * {0}: {1} ({2})'.format(i + 1, name, provider), bold=True)
        else:
            click.echo('    {0}: {1} ({2})'.format(i + 1, name, provider))

    click.echo('')


def _select(config, machine, machines):
    # Select by name
    if config.has_machine(machine):
        config.set_selected(machine)
        config.save_state()
        return

    # Select by index
    try:
        index = int(machine)
    except ValueError:
        raise InvalidArgumentException('Unable to select machine "{0}".'.format(machine))

    index -= 1
    if 0 <= index < len(machines):
        config.set_selected(machines[index])
        config.save_state()
        return

    raise InvalidArgumentException('Unable to select machine "{0}".'.format(machine))

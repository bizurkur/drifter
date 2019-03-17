"""List available machines."""
from __future__ import absolute_import, division, print_function

import click

import drifter.commands
from drifter.exceptions import InvalidArgumentException


@click.command(name='list')
@click.option('--select', help='Selects a machine')
@click.option('--no-select', help='Selects no machines', is_flag=True)
@drifter.commands.pass_config
@click.pass_context
def list_command(ctx, config, select, no_select):
    """List available machines."""
    machines = config.list_machines()
    machines.sort()

    if not machines:
        click.echo('No machines available. Use `drifter up` to create one.')

        return

    if select:
        _select(config, select, machines)
    elif no_select:
        config.select_machine(None)
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
        config.select_machine(machine)
        config.save_state()

        return

    # Select by index
    try:
        index = int(machine)
    except ValueError:
        raise InvalidArgumentException('Unable to select machine "{0}".'.format(machine))

    index -= 1
    if 0 <= index < len(machines):
        config.select_machine(machines[index])
        config.save_state()

        return

    raise InvalidArgumentException('Unable to select machine "{0}".'.format(machine))

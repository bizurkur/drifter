from __future__ import print_function, absolute_import, division

import click

import drifter.commands
from drifter.exceptions import InvalidArgumentException


@click.command()
@click.option('--select', help='Selects a machine')
@click.option('--no-select', help='Selects no machines', is_flag=True)
@drifter.commands.pass_config
@click.pass_context
def list(ctx, config, select, no_select):
    """Lists available machines."""

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
            click.secho('  * %d: %s (%s)' % (i + 1, name, provider), bold=True)
        else:
            click.echo('    %d: %s (%s)' % (i + 1, name, provider))

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
        raise InvalidArgumentException('Unable to select machine "%s".' % (machine))

    index -= 1
    if 0 <= index < len(machines):
        config.select_machine(machines[index])
        config.save_state()

        return

    raise InvalidArgumentException('Unable to select machine "%s".' % (machine))

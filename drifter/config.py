"""Handle configuration settings."""
from __future__ import absolute_import, division, print_function

import io
import json
import os
import sys

import click

import yaml

from drifter.exceptions import GenericException, InvalidArgumentException


class Config(object):
    """Handle configuration settings."""

    def __init__(self, folder=None):
        """Set up the configuration handles."""
        self.state = {}
        self.base_dir = folder or os.getcwd()
        self.state_dir = '.drifter'
        self.state_file = 'state.json'
        self.defaults = {}
        self.defaults_file = 'drifter.yaml'
        self.defaults_loaded = False

    def get_state_path(self, path=None):
        """Get the path to the state file."""
        if not path:
            path = self.base_dir

        return os.path.join(path, self.state_dir, self.state_file)

    def get_state_dir(self):
        """Get the path to the state file directory."""
        return os.path.join(self.base_dir, self.state_dir)

    def load_state(self, path=None):
        """Load the state file."""
        if not path:
            self._find_state_dir()
            path = self.get_state_path()

        if not os.path.isfile(path):
            return

        try:
            with io.open(path, 'r') as handle:
                self.state = json.load(handle)
        except IOError:
            click.secho(
                'State file "{0}" is not readable. Check your file permissions.'.format(path),
                fg='red',
                bold=True,
            )
            sys.exit(1)
        except ValueError:
            click.secho(
                'State file "{0}" seems to have invalid data.'.format(path),
                fg='red',
                bold=True,
            )
            if click.confirm('Would you like to reset it?'):
                self._reset_state()
            else:
                click.echo('Aborted!')
                sys.exit(1)

    def save_state(self):
        """Save the state file."""
        filename = self.get_state_path()
        with io.open(filename, 'w', encoding='utf-8') as handle:
            data = json.dumps(self.state, sort_keys=True, indent=4, separators=(',', ': '))
            handle.write(unicode(data))

    def add_machine(self, name, settings):
        """Add a machine."""
        self.state['machines'][name] = settings

    def remove_machine(self, name):
        """Remove a machine."""
        if name in self.state['machines']:
            del self.state['machines'][name]

    def has_machine(self, name):
        """Check if a machine exists."""
        if name in self.state['machines']:
            return True

        return False

    def get_machine(self, name):
        """Get metadata for a machine."""
        if name in self.state['machines']:
            return self.state['machines'][name]

        raise GenericException('Machine "{0}" does not exist.'.format(name))

    def list_machines(self, provider=None):
        """List all available machines.

        Optionally, machines can be limited to a specific provider.
        """
        machines = self.state['machines'].keys()
        if not provider:
            return machines

        provider_machines = []
        for machine in machines:
            if provider == self.get_machine(machine).get('provider', None):
                provider_machines.append(machine)

        return provider_machines

    def set_selected(self, name):
        """Set the given machine as selected."""
        self.state['selected'] = name

    def get_selected(self):
        """Get the selected machine.

        Checks for environment variable DRIFTER_NAME, then the state file.
        """
        return os.environ.get('DRIFTER_NAME', self.state.get('selected', None))

    def get_provider(self, name):
        """Get the provider for a machine."""
        settings = self.get_machine(name)
        provider = settings.get('provider', None)
        if not provider:
            raise GenericException('No provider set for the "{0}" machine.'.format(name))

        return provider

    def get_machine_default(self, machine_name, setting_name, default=None):
        """Get a machine-specific default, with fallback to the global default."""
        # Get machine-specific setting
        setting = self.get_default('machines.{0}.{1}'.format(machine_name, setting_name))
        if setting is not None:
            return setting

        # Get global setting
        return self.get_default(setting_name, default)

    def get_default(self, name, default=None):
        """Get the default value to use for a setting.

        Use dots to traverse nested dictionary values.
        """
        if not self.defaults_loaded:
            self._load_defaults()
            self.defaults_loaded = True

        if not isinstance(name, str) and not isinstance(name, unicode):
            raise InvalidArgumentException(
                'Failed to load default value. Name must be a string.',
            )

        parts = name.split('.')
        data = self.defaults
        for part in parts:
            if not isinstance(data, dict) or part not in data:
                return default

            data = data[part]

        return data

    def _load_defaults(self):
        self.defaults = {}

        path = os.path.join(self.base_dir, self.defaults_file)
        if not os.path.isfile(path):
            return

        try:
            with io.open(path, 'r') as handle:
                self.defaults = yaml.safe_load(handle)
        except IOError:
            raise GenericException(
                'State file "{0}" is not readable. Check your file permissions.'.format(path),
            )

    def _find_state_dir(self, path=None):
        """Find the state file.

        Recursively looks in parent directories until the directory is located.
        """
        if not path:
            path = self.base_dir

        filename = self.get_state_path(path)
        if os.path.exists(filename):
            self.base_dir = path

            return

        parent = os.path.dirname(path)
        if parent and parent != path:
            return self._find_state_dir(parent)

        self._init_state()

    def _init_state(self):
        """Create a state file, if one doesn't already exist."""
        state_dir = self.get_state_dir()
        if not os.path.exists(state_dir):
            os.mkdir(state_dir)

        filename = self.get_state_path()
        if not os.path.isfile(filename):
            self._reset_state()
            self.save_state()

    def _reset_state(self):
        """Reset the state."""
        self.state = {
            'selected': None,
            'machines': {},
        }

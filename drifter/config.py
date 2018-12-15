
from __future__ import print_function, absolute_import, division
import io
import json
import os
import sys

import click

from drifter.exceptions import GenericException

class Config(object):
    def __init__(self, folder=None):
        self.data = {}
        self.base_dir = folder or os.getcwd()
        self.config_dir = '.drifter'
        self.config_file = 'config.json'

    def get_path(self, path=None):
        """Gets the path to the configuration file."""
        if not path:
            path = self.base_dir

        return os.path.join(path, self.config_dir, self.config_file)

    def get_dir(self):
        """Gets the path to the configuration file directory."""
        return os.path.join(self.base_dir, self.config_dir)

    def load(self, path=None):
        """Loads the configuration file."""
        if not path:
            self.find()
            path = self.get_path()

        if os.path.isfile(path):
            try:
                with io.open(path, 'r') as handle:
                    self.data = json.load(handle)
            except IOError as e:
                click.secho(
                    'Configuration file "%s" is not readable.' % (path)
                        +' Check your file permissions.',
                    fg='red',
                    bold=True
                )
                sys.exit(1)
            except ValueError as e:
                click.secho(
                    'Configuration file "%s" seems to have invalid data.' % (path),
                    fg='red',
                    bold=True
                )
                if click.confirm('Would you like to reset it?'):
                    self.create()
                else:
                    click.echo('Aborted!')
                    sys.exit(1)

    def find(self, path=None):
        """Finds the configuration file.
        Recursively looks in parent directories until a config is located.
        """
        if not path:
            path = self.base_dir

        filename = self.get_path(path)
        if os.path.exists(filename):
            self.base_dir = path

            return None

        parent = os.path.dirname(path)
        if parent and parent != path:
            return self.find(parent)

        self.init()

    def init(self):
        """Creates a configuration file."""
        config_dir = self.get_dir()
        if not os.path.exists(config_dir):
            os.mkdir(config_dir)

        filename = self.get_path()
        if not os.path.isfile(filename):
            self.create()
            self.save()

    def create(self):
        """Creates empty configuration settings."""
        self.data = {
            'defaults': {},
            'selected': None,
            'machines': {}
        }

    def save(self):
        """Saves the configuration file."""
        filename = self.get_path()
        with io.open(filename, 'w', encoding='utf-8') as handle:
            data = json.dumps(self.data, sort_keys=True, indent=4, separators=(',', ': '))
            handle.write(unicode(data))

    def add_machine(self, name, settings):
        self.data['machines'][name] = settings

    def remove_machine(self, name):
        if name in self.data['machines']:
            del self.data['machines'][name]

    def get_machine(self, name):
        if name in self.data['machines']:
            return self.data['machines'][name]

        raise GenericException('Machine "%s" does not exist.' % (name))

    def get_provider(self, name):
        settings = self.get_machine(name)
        provider = settings.get('provider', None)
        if not provider:
            raise GenericException(
                'No provider set for "%s" machine.' % (name)
            )

        return provider

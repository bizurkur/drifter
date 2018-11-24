
from __future__ import print_function, absolute_import, division
import io
import os
import yaml

class Config(object):
    def __init__(self, folder=None):
        self.data = {}
        self.base_dir = folder or os.getcwd()
        self.config_dir = '.drifter'
        self.config_file = 'config.yaml'

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
            with io.open(path, 'r') as handle:
                self.data = yaml.load(handle)

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
            yaml.dump(self.data, handle, default_flow_style=False)

    def add_machine(self, name, settings):
        self.data['machines'][name] = settings

    def remove_machine(self, name):
        if name in self.data['machines']:
            del self.data['machines'][name]

    def get_machine(self, name):
        if name in self.data['machines']:
            return self.data['machines'][name]

        raise Exception('Machine "%s" does not exist.' % (name))

    def get_provider(self, name):
        settings = self.get_machine(name)
        provider = settings.get('provider', None)
        if not provider:
            raise Exception('No provider set for "%s" machine.' % (name))

        return provider

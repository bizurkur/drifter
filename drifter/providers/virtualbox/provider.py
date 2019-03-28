"""Provide interaction with the VirtualBox SDK."""
from __future__ import absolute_import, division, print_function

import logging
import os
import re
from configparser import ConfigParser
from time import sleep

from defusedxml import minidom

import six

from drifter.exceptions import InvalidArgumentException, ProviderException
from drifter.utils import get_cli


class VirtualBoxException(ProviderException):
    """Exception to represent a VirtualBox error."""

    pass


class Provider(object):
    """Provide interaction with the VirtualBox SDK."""

    def __init__(self):
        """Set up the VirtualBox connection."""
        self.cache = {}

    def load_machine(self, name, silent=False):
        """Load a machine for usage and make sure it's accessible."""
        logging.debug('Loading machine "%s"...', name)

        try:
            data = self._list_vms()
        except VirtualBoxException as e:
            logging.debug('Failed to load machine.')
            if silent:
                return False

            raise e

        if name in data:
            logging.debug('Machine loaded.')
            return True

        logging.debug('Failed to load machine.')
        if silent:
            return False

        raise VirtualBoxException('Machine "{0}" is not available.'.format(name))

    def is_running(self, name):
        """Check if a machine is running."""
        logging.debug('Checking if machine is running...')

        running = self._list_running_vms()
        if name in running:
            logging.debug('Machine is running.')
            return True

        logging.debug('Machine is not running.')
        return False

    def create(self, name, os_type):
        """Create a machine and register it with VirtualBox."""
        logging.debug('Creating machine "%s"...', name)

        res, code = get_cli(['vboxmanage', 'createvm', '--name', name, '--ostype', os_type, '--register'])
        if code != 0:
            logging.debug('Create failed. Aborting...')
            self._raise_exception('Failed to create machine', res)

        logging.debug('Machine created.')

        self._clear_vms()

        return self._get_machine_info(name)

    def clone_from(self, name, disks):
        """Clone a list of disks into the machine.

        Disks should be a list of paths to valid VirtualBox disk files.
        """
        logging.debug('Cloning disks...')

        port_count = len(disks)
        self._create_storage(name, port_count)

        port = 0
        for disk in disks:
            self._create_disk_clone(name, disk, port)
            port += 1

        logging.debug('Cloning complete.')

    def destroy(self, name):
        """Destroy a machine."""
        logging.debug('Destroying machine...')

        self.stop(name)

        res, code = get_cli(['vboxmanage', 'unregistervm', name, '--delete'])
        if code != 0:
            self._raise_exception('Failed to destroy machine', res)

        self._clear_vms()
        self._clear_running_vms()

        logging.debug('Machine destroyed.')

    def start(self, name, head=False, memory=None, mac=None, ports=None):
        """Start a machine."""
        logging.debug('Starting machine...')
        if self.is_running(name):
            return True

        self._set_boot(name, memory)
        self._configure_networks(name, mac)
        self._forward_ports(name, ports)

        logging.debug('Launching machine...')

        res, code = get_cli(['vboxmanage', 'startvm', name, '--type', 'gui' if head else 'headless'])
        if code != 0:
            self._raise_exception('Failed to start machine', res)

        self._clear_running_vms()

        logging.debug('Machine started.')

        return True

    def stop(self, name):
        """Stop a machine."""
        logging.debug('Stopping machine...')
        if not self.is_running(name):
            return True

        # Attempt graceful shutdown
        logging.debug('Attempting graceful shutdown...')
        res, code = get_cli(['vboxmanage', 'controlvm', name, 'acpipowerbutton'])
        if code != 0:
            # Force shutdown
            logging.debug('Graceful shutdown failed. Forcing power off...')
            res, code = get_cli(['vboxmanage', 'controlvm', name, 'poweroff'])
            if code != 0:
                self._raise_exception('Failed to shutdown machine', res)

        count = 0
        self._clear_running_vms()
        while self.is_running(name):
            count += 1
            if count >= 30:
                count = 0
                # Assume if the machine is still running after 30 secs, something went wrong.
                # Force a shutdown just to be safe.
                logging.debug('Forcing power off...')
                res, code = get_cli(['vboxmanage', 'controlvm', name, 'poweroff'])
                if code != 0:
                    self._raise_exception('Failed to shutdown machine', res)

            self._clear_running_vms()
            sleep(1)

        logging.debug('Machine stopped.')

        return True

    def get_server_data(self, name, require_ssh=True):
        """Get machine metadata and connection information."""
        logging.debug('Getting machine data for "%s"...', name)

        server = {
            'redirects': [],
        }

        data = self._get_machine_info(name)
        for key, value in six.iteritems(data):
            if not key.startswith('forwarding('):
                continue

            parts = value.split(',')
            server['redirects'].append({
                'name': parts[0],
                'protocol_id': parts[1],
                'host_name': parts[2],
                'host_port': parts[3],
                'guest_name': parts[4],
                'guest_port': parts[5],
            })
            if parts[5] == '22':
                server['ssh_host'] = parts[2]
                server['ssh_port'] = parts[3]

        if require_ssh and not server.get('ssh_port', None):
            raise ProviderException('Machine has no SSH port defined.')

        return server

    def get_base_metadata(self, base):
        """Read the XML file for a base machine and return the metadata."""
        logging.debug('Detecting metadata for "%s"...', base)

        os_type = None
        media = []

        machine = None
        for path in os.listdir(base):
            filename = os.path.join(base, path)
            if not os.path.isfile(filename):
                continue

            if filename.endswith('.vbox'):
                xml = minidom.parse(filename)
                machines = xml.getElementsByTagName('Machine')
                if machines:
                    machine = machines[0]
                break

        if not machine:
            raise VirtualBoxException(
                'Unable to find settings for "{0}".'.format(base),
            )

        os_type = machine.attributes.get('OSType', None)
        if not os_type:
            raise VirtualBoxException(
                'Unable to determine "{0}" OS type.'.format(base),
            )
        logging.debug('Detected OS as "%s"', os_type.value)

        disks = machine.getElementsByTagName('HardDisk')
        for disk in disks:
            loc = disk.attributes.get('location', None)
            if loc:
                logging.debug('Detected disk "%s"', loc.value)
                media.append(os.path.join(base, loc.value))

        if not media:
            raise ProviderException('Base machine has no disks.')

        return {
            'os': os_type.value,
            'media': media,
        }

    def _create_storage(self, name, port_count):
        logging.debug('Creating storage for %s disks...', port_count)

        res, code = get_cli(['vboxmanage', 'storagectl', name, '--name', 'SATAController',
                             '--add', 'sata', '--portcount', port_count, '--hostiocache', 'on'])
        if code != 0:
            self._raise_exception('Failed to create machine storage', res)

        logging.debug('Storage created.')

    def _create_disk_clone(self, name, filename, port):
        basename = os.path.basename(filename)
        logging.debug('Cloning disk "%s"...', basename)

        data = self._get_machine_info(name)
        settings_file = data.get('cfgfile', None)
        if not settings_file:
            raise VirtualBoxException('Unable to locate settings for machine.')

        machine_dir = os.path.dirname(settings_file)
        medium_path = os.path.join(machine_dir, basename)

        def _cleanup(medium_path):
            if not os.path.exists(medium_path):
                return
            logging.debug('Removing medium "%s"...', medium_path)
            get_cli(['vboxmanage', 'closemedium', 'disk', medium_path, '--delete'])
            if os.path.exists(medium_path):
                os.remove(medium_path)

        logging.debug('Cloning source to destination...')
        res, code = get_cli(['vboxmanage', 'clonemedium', 'disk', filename, medium_path])
        if code != 0:
            _cleanup(medium_path)
            self._raise_exception('Failed to clone source medium', res)

        logging.debug('Attaching device...')
        res, code = get_cli(['vboxmanage', 'storageattach', name, '--storagectl',
                             'SATAController', '--port', port, '--type', 'hdd',
                             '--device', 0, '--medium', medium_path])
        if code != 0:
            _cleanup(medium_path)
            self._raise_exception('Failed to attach device', res)

        # clear any cached data
        self._clear_machine_info(name)

        logging.debug('Disk cloned.')

    def _set_boot(self, name, memory):
        if not memory:
            memory = 512

        logging.debug('Setting memory to %s...', memory)
        res, code = get_cli(['vboxmanage', 'modifyvm', name, '--memory', memory,
                             '--boot1', 'disk', '--boot2', 'none', '--boot3', 'none', '--boot4', 'none'])
        if code != 0:
            self._raise_exception('Failed to update machine settings', res)

        logging.debug('Settings saved.')

    def _configure_networks(self, name, nat_mac):
        logging.debug('Configuring network(s)...')

        logging.debug('Creating NAT...')
        res, code = get_cli(['vboxmanage', 'modifyvm', name, '--nic1', 'nat',
                             '--macaddress1', nat_mac if nat_mac else 'auto'])
        if code != 0:
            self._raise_exception('Failed to create NAT network', res)

        logging.debug('NAT created.')
        logging.debug('Network(s) configured.')

    def _forward_ports(self, name, port_string):
        orig_list = self._parse_ports(port_string)
        port_list = self._get_collision_free_ports(name, orig_list)

        logging.debug('Forwarding ports...')

        command = []
        data = self._get_machine_info(name)
        for key, value in six.iteritems(data):
            if not key.startswith('forwarding('):
                continue

            parts = value.split(',', 2)
            command += ['--natpf1', 'delete', parts[0]]

        if command:
            res, code = get_cli(['vboxmanage', 'modifyvm', name] + command)
            if code != 0:
                self._raise_exception('Failed to remove existing forwarded ports', res)

        command = []
        count = 1
        for ports in port_list:
            logging.debug('Forwarding port %s (host) to %s (guest)...', ports['host'], ports['guest'])
            pf_name = '{0}:{1}:{2}'.format(
                ports['host'],
                ports['guest'],
                ports['protocol'],
            )
            command += ['--natpf{:d}'.format(count), '{0},{1},{2},{3},,{4}'.format(
                pf_name, ports['protocol'], '127.0.0.1', ports['host'], ports['guest'],
            )]

        if command:
            res, code = get_cli(['vboxmanage', 'modifyvm', name] + command)
            if code != 0:
                self._raise_exception('Failed to forward ports', res)

        # clear any cached data
        self._clear_machine_info(name)

        logging.debug('Ports forwarded.')

    def _merge_ports(self, ports):
        return ','.join(
            ['{0}:{1}:{2}'.format(
                port['host'],
                port['guest'],
                port.get('protocol', 'tcp'),
            ) for port in ports],
        )

    def _parse_ports(self, ports):
        port_list = []
        if not ports:
            ports = ''
        elif isinstance(ports, list):
            ports = self._merge_ports(ports)

        allowed_protocols = ['tcp', 'udp']

        has_ssh = False
        parts = ports.split(',')
        for part in parts:
            if part == '':
                continue
            pieces = part.split(':')
            host_port = None
            guest_port = None
            protocol = 'tcp'
            count = len(pieces)
            if count > 3 or count < 2:
                raise InvalidArgumentException(
                    'Value "{0}" is invalid. '.format(part)
                    + 'Expected <host-port>:<guest-port>[:<protocol>]',
                )

            host_port = self._validate_port(pieces[0])
            guest_port = self._validate_port(pieces[1])
            if count >= 3:
                protocol = self._validate_proto(pieces[2], allowed_protocols)

            if guest_port == 22:
                has_ssh = True

            port_list.append({
                'host': host_port,
                'guest': guest_port,
                'protocol': protocol,
            })

        if not has_ssh:
            port_list.append({
                'host': 2222,
                'guest': 22,
                'protocol': 'tcp',
            })

        return port_list

    def _validate_port(self, port):
        error = 'Port "{0}" is invalid; must be an integer 1-65535.'.format(port)

        try:
            port = int(port)
        except Exception:
            raise InvalidArgumentException(error)

        if port <= 0 or port > 65535:
            raise InvalidArgumentException(error)

        return port

    def _validate_proto(self, proto, allowed):
        protocol = proto.lower()
        if protocol not in allowed:
            raise InvalidArgumentException(
                'Protocol "{0}" is invalid; must be one of ["{1}"]'.format(
                    protocol,
                    '", "'.join(allowed),
                ),
            )

        return protocol

    def _get_collision_free_ports(self, name, port_list):
        """Ensure all ports won't conflict with other machines."""
        logging.debug('Detecting collision free ports...')

        used_ports = []
        for machine in six.iterkeys(self._list_vms()):
            if name == machine:
                # Ignore self
                continue

            data = self.get_server_data(machine, False)
            for redirect in data.get('redirects', []):
                try:
                    used_ports.append(int(redirect['host_port']))
                except Exception:
                    pass

        for port in port_list:
            port['host'] = self._get_collision_free_port(port['host'], used_ports)

        return port_list

    def _get_collision_free_port(self, port, used_ports):
        """Get a port number that won't conflict with other machines."""
        while port in used_ports:
            logging.debug('Port %s is in use. Trying %s...', port, port + 1)
            port += 1

        return port

    def _clear_vms(self):
        if 'vms' in self.cache:
            del self.cache['vms']

    def _list_vms(self):
        cached_vms = self.cache.get('vms', None)
        if cached_vms:
            return cached_vms

        res, code = get_cli(['vboxmanage', 'list', 'vms'])
        if code != 0:
            raise VirtualBoxException('No machines available.')

        cached_vms = {}

        if res:
            matches = re.findall(r'\"([^\"]+)\" \{([^\}]+)\}', res)
            for item in matches:
                # name => uuid
                cached_vms[item[0]] = item[1]

        self.cache.setdefault('vms', cached_vms)

        return cached_vms

    def _clear_running_vms(self):
        if 'runningvms' in self.cache:
            del self.cache['runningvms']

    def _list_running_vms(self):
        cached_vms = self.cache.get('runningvms', None)
        if cached_vms:
            return cached_vms

        res, code = get_cli(['vboxmanage', 'list', 'runningvms'])
        if code != 0:
            raise VirtualBoxException('No machines available.')

        cached_vms = {}

        if res:
            matches = re.findall(r'\"([^\"]+)\" \{([^\}]+)\}', res)
            for item in matches:
                # name => uuid
                cached_vms[item[0]] = item[1]

        self.cache.setdefault('runningvms', cached_vms)

        return cached_vms

    def _clear_machine_info(self, name):
        info = self.cache.get('info', None)
        if info is None:
            return

        if name in info:
            del info[name]

    def _get_machine_info(self, name):
        cached_info = self.cache.get('info', {}).get(name, None)
        if cached_info:
            return cached_info

        res, code = get_cli(['vboxmanage', 'showvminfo', name, '--machinereadable'])
        if code != 0:
            raise VirtualBoxException('Machine not found.')

        parser = ConfigParser()
        parser.read_string(unicode('[DEFAULT]\n' + res))

        cached_info = {}
        for item in parser.items('DEFAULT'):
            cached_info[item[0].strip('"')] = item[1].strip('"')

        self.cache.setdefault('info', {})
        self.cache['info'].setdefault(name, cached_info)

        return cached_info

    def _raise_exception(self, message, res):
        print(res)
        errors = re.findall(r'VBoxManage: error: ([^\n]+)', res)
        if not errors:
            raise VirtualBoxException(
                '{0}: unknown error.'.format(message),
            )

        raise VirtualBoxException(
            '{0}: {1}'.format(message, errors[0]),
        )

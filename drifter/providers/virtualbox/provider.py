"""Provide interaction with the VirtualBox SDK."""
from __future__ import absolute_import, division, print_function

import logging
import os
from time import sleep

from defusedxml import minidom

# pylint: disable=import-error
import vboxapi

from drifter.exceptions import InvalidArgumentException, ProviderException


class VirtualBoxException(ProviderException):
    """Exception to represent a VirtualBox error."""

    pass


class Provider(object):
    """Provide interaction with the VirtualBox SDK."""

    def __init__(self):
        """Set up the VirtualBox connection."""
        self.manager = vboxapi.VirtualBoxManager(None, None)
        self.vbox = self.manager.getVirtualBox()
        self.session = self.manager.getSessionObject(self.vbox)
        self.machine = None

    def load_machine(self, name, silent=False):
        """Load a machine for usage and make sure it's accessible."""
        logging.debug('Loading machine "%s"...', (name))
        try:
            self.machine = self.vbox.findMachine(name)
        except Exception as e:
            logging.debug('Failed to load machine.')
            if silent:
                return False

            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException(message)

        logging.debug('Checking machine accessibility...')
        if not self.machine.accessible:
            raise VirtualBoxException(
                'Machine is not accessible: {0}'.format(self.machine.accessError),
            )

        logging.debug('Machine loaded.')
        return True

    def acquire_lock(self, write=False):
        """Acquire the machine lock."""
        if write:
            logging.debug('Acquiring write lock...')
            self.machine.lockMachine(self.session, self.manager.constants.LockType_Write)
        else:
            logging.debug('Acquiring shared lock...')
            self.machine.lockMachine(self.session, self.manager.constants.LockType_Shared)

        logging.debug('Lock acquired.')

    def release_lock(self):
        """Release the machine lock."""
        logging.debug('Releasing lock...')

        try:
            self.session.unlockMachine()
        except Exception:
            logging.debug('Failed to release lock?')

        # Give it a moment to release the lock
        sleep(.5)

        logging.debug('Lock released.')

    def is_running(self):
        """Check if a machine is running."""
        logging.debug('Checking if machine is running...')

        if self.machine.state < self.manager.constants.MachineState_FirstOnline:
            logging.debug('Machine is not running.')
            return False

        if self.machine.state > self.manager.constants.MachineState_LastOnline:
            logging.debug('Machine is not running.')
            return False

        logging.debug('Machine is running.')
        return True

    def create(self, name, os_type):
        """Create a machine and register it with VirtualBox."""
        logging.debug('Creating machine "%s"...', (name))

        try:
            self.machine = self.vbox.createMachine('', name, [], os_type, '')
        except Exception as e:
            logging.debug('Create failed. Aborting...')

            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException(
                'Failed to create machine: {0}'.format(message),
            )

        logging.debug('Registering machine...')
        try:
            self.vbox.registerMachine(self.machine)
        except Exception as e:
            # Clean up any data that was saved
            logging.debug('Registration failed. Cleaning up...')
            try:
                progress = self.machine.deleteConfig([])
                progress.waitForCompletion(-1)
            except Exception as _e:
                message = getattr(_e, 'msg', e.message)
                raise VirtualBoxException(
                    'Failed to clean up registration: {0}'.format(message),
                )

            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException(
                'Failed to register machine: {0}'.format(message),
            )

    def clone_from(self, disks):
        """Clone a list of disks into the machine.

        Disks should be a list of paths to valid VirtualBox disk files.
        """
        logging.debug('Creating disk clones...')

        port_count = len(disks)
        storage = self._create_storage(port_count)

        port = 0
        for disk in disks:
            self._create_disk_clone(disk, storage, port)
            port += 1

    def destroy(self):
        """Destroy a machine."""
        logging.debug('Destroying machine...')

        self.stop()

        logging.debug('Unregistering machine...')
        try:
            mediums = self.machine.unregister(
                self.manager.constants.CleanupMode_DetachAllReturnHardDisksOnly,
            )
        except Exception as e:
            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException(
                'Failed to unregister machine: {0}'.format(message),
            )
        logging.debug('Machine unregistered.')

        logging.debug('Deleting files...')
        try:
            progress = self.machine.deleteConfig(mediums)
            progress.waitForCompletion(-1)
        except Exception as e:
            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException(
                'Failed to delete files for machine: {0}'.format(message),
            )
        logging.debug('Files deleted.')

    def start(self, head=False, memory=None, mac=None, ports=None):
        """Start a machine."""
        logging.debug('Starting machine...')
        if self.is_running():
            return

        if self.machine.state != self.manager.constants.MachineState_Saved:
            self._set_boot(memory)
            self._configure_networks(mac)
            self._forward_ports(ports)

        logging.debug('Launching machine...')
        try:
            progress = self.machine.launchVMProcess(
                self.session,
                'gui' if head else 'headless',
                '',
            )
            progress.waitForCompletion(-1)
        except Exception as e:
            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException('Failed to start machine: {0}'.format(message))
        finally:
            self.release_lock()

    def stop(self):
        """Stop a machine."""
        logging.debug('Stopping machine...')
        if not self.is_running():
            return True

        try:
            self.acquire_lock()

            logging.debug('Forcing a shutdown...')
            progress = self.session.console.powerDown()
            progress.waitForCompletion(-1)
            logging.debug('Shutdown complete.')
        except Exception as e:
            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException(
                'Failed to shutdown machine: {0}'.format(message),
            )
        finally:
            self.release_lock()

        logging.debug('Machine stopped.')
        return True

    def get_server_data(self):
        """Get machine metadata and connection information."""
        logging.debug('Getting machine data...')

        server = {
            'redirects': [],
        }

        try:
            self.acquire_lock()

            network = self.session.machine.getNetworkAdapter(0)

            redirects = network.NATEngine.getRedirects()
            for redirect in redirects:
                parts = redirect.split(',')
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

        except Exception as e:
            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException('Failed to get server data: {0}'.format(message))
        finally:
            self.release_lock()

        if not server.get('ssh_port', None):
            raise ProviderException('Machine has no SSH port defined.')

        return server

    def get_base_metadata(self, base):
        """Read the XML file for a base machine and return the metadata."""
        logging.debug('Detecting settings for "%s"...', (base))

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

        disks = machine.getElementsByTagName('HardDisk')
        for disk in disks:
            loc = disk.attributes.get('location', None)
            if loc:
                media.append(os.path.join(base, loc.value))

        if not media:
            raise ProviderException('Base machine has no disks.')

        return {
            'os': os_type.value,
            'media': media,
        }

    def _create_storage(self, port_count):
        logging.debug('Creating storage...')

        try:
            self.acquire_lock()

            storage = self.session.machine.addStorageController(
                'SATAController',
                self.manager.constants.StorageBus_SATA,
            )
            storage.portCount = port_count
            storage.useHostIOCache = True

            self.session.machine.saveSettings()
        except Exception as e:
            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException(
                'Unable to create machine storage: {0}'.format(message),
            )
        finally:
            self.release_lock()

        return storage

    def _create_disk_clone(self, filename, storage, port):
        basename = os.path.basename(filename)
        logging.debug('Cloning disk "%s"...', (basename))

        machine_dir = os.path.dirname(self.machine.settingsFilePath)
        medium_path = os.path.join(machine_dir, basename)

        try:
            self.acquire_lock()

            extension = os.path.splitext(filename)[1].lstrip('.')

            medium = self.vbox.createMedium(
                extension,
                medium_path,
                self.manager.constants.AccessMode_ReadWrite,
                self.manager.constants.DeviceType_HardDisk,
            )

            parent = self.vbox.openMedium(
                filename,
                self.manager.constants.DeviceType_HardDisk,
                self.manager.constants.AccessMode_ReadOnly,
                False,
            )

            progress = parent.cloneToBase(medium, [self.manager.constants.MediumVariant_Standard])
            progress.waitForCompletion(-1)

            self.session.machine.attachDevice(
                storage.name,
                port,
                0,
                self.manager.constants.DeviceType_HardDisk,
                medium,
            )
            self.session.machine.saveSettings()
        except Exception as e:
            logging.debug('Failed to clone disk.')
            if os.path.exists(medium_path):
                logging.debug('Removing medium "%s"...', (medium_path))
                os.remove(medium_path)

            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException(
                'Unable to create machine media: {0}'.format(message),
            )
        finally:
            self.release_lock()

    def _set_boot(self, memory):
        logging.debug('Saving machine settings...')

        if not memory:
            memory = 512

        try:
            self.acquire_lock()

            self.session.machine.memorySize = memory
            self.session.machine.setBootOrder(1, self.manager.constants.DeviceType_HardDisk)
            self.session.machine.setBootOrder(2, self.manager.constants.DeviceType_Null)
            self.session.machine.setBootOrder(3, self.manager.constants.DeviceType_Null)
            self.session.machine.setBootOrder(4, self.manager.constants.DeviceType_Null)
            self.session.machine.saveSettings()
        except Exception as e:
            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException(
                'Unable to set machine settings: {0}'.format(message),
            )
        finally:
            self.release_lock()

    def _configure_networks(self, nat_mac):
        logging.debug('Configuring network(s)...')
        try:
            self.acquire_lock()

            network_a = self.session.machine.getNetworkAdapter(0)
            network_a.attachmentType = self.manager.constants.NetworkAttachmentType_NAT
            network_a.enabled = True
            network_a.cableConnected = True
            if nat_mac:
                network_a.MACAddress = nat_mac

            # network_b = self.session.machine.getNetworkAdapter(1)
            # network_b.attachmentType = self.manager.constants.NetworkAttachmentType_HostOnly
            # network_b.enabled = True
            # network_b.cableConnected = True
            # network_b.hostOnlyInterface = 'vboxnet0'

            self.session.machine.saveSettings()
        except Exception as e:
            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException(
                'Failed to configure network: {0}'.format(message),
            )
        finally:
            self.release_lock()

    def _forward_ports(self, port_string):
        orig_list = self._parse_ports(port_string)
        port_list = self._get_collision_free_ports(orig_list)

        logging.debug('Forwarding ports...')
        try:
            self.acquire_lock()

            network = self.session.machine.getNetworkAdapter(0)

            redirects = network.NATEngine.getRedirects()
            for redirect in redirects:
                parts = redirect.split(',', 2)
                network.NATEngine.removeRedirect(parts[0])

            for ports in port_list:
                network.NATEngine.addRedirect(
                    '{0}:{1}:{2}'.format(
                        ports['host'],
                        ports['guest'],
                        ports['protocol'],
                    ),
                    ports['protocol_id'],
                    '127.0.0.1',
                    ports['host'],
                    '',
                    ports['guest'],
                )

            self.session.machine.saveSettings()
        except Exception as e:
            message = getattr(e, 'msg', e.message)
            raise VirtualBoxException('Failed to forward ports: {0}'.format(message))
        finally:
            self.release_lock()

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

        allowed_protocols = {
            'tcp': self.manager.constants.NATProtocol_TCP,
            'udp': self.manager.constants.NATProtocol_UDP,
        }

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
                'protocol_id': allowed_protocols[protocol],
            })

        if not has_ssh:
            port_list.append({
                'host': 2222,
                'guest': 22,
                'protocol': 'tcp',
                'protocol_id': allowed_protocols['tcp'],
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
                    '", "'.join(allowed.keys()),
                ),
            )

        return protocol

    def _get_collision_free_ports(self, port_list):
        """Ensure all ports won't conflict with other machines."""
        for port in port_list:
            port['host'] = self._get_collision_free_port(port['host'])

        return port_list

    def _get_collision_free_port(self, port):
        """Get a port number that won't conflict with other machines."""
        used_ports = []

        machines = self.vbox.getMachines()
        for machine in machines:
            if machine.id == self.machine.id:
                # Ignore self
                continue

            network = machine.getNetworkAdapter(0)
            redirects = network.NATEngine.getRedirects()
            for redirect in redirects:
                parts = redirect.split(',')
                if len(parts) < 5:
                    continue
                try:
                    used_ports.append(int(parts[3]))
                except Exception:
                    pass

        while port in used_ports:
            logging.debug('Port {0} is in use. Trying {1}...'.format(port, port + 1))
            port += 1

        return port

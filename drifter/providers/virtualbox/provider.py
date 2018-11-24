import logging
import os
import sys
from time import sleep
import vboxapi

class Provider(object):
    def __init__(self):
        self.manager = vboxapi.VirtualBoxManager(None, None)
        self.vbox = self.manager.getVirtualBox()
        self.session = self.manager.getSessionObject(self.vbox)
        self.machine = None

    def load_machine(self, name, silent=False):
        logging.debug('Loading machine "%s"...' % (name))
        try:
            self.machine = self.vbox.findMachine(name)
        except Exception as e:
            logging.debug('Failed to load machine.')
            if silent:
                return False

            message = getattr(e, 'msg', e.message)
            raise Exception(message)

        logging.debug('Checking machine accessibility...')
        if not self.machine.accessible:
            raise Exception(
                'Machine is not accessible: %s' % (self.machine.accessError)
            )

        logging.debug('Machine loaded.')
        return True

    def acquire_lock(self, write=False):
        if write:
            logging.debug('Acquiring write lock...')
            self.machine.lockMachine(self.session, self.manager.constants.LockType_Write)
        else:
            logging.debug('Acquiring shared lock...')
            self.machine.lockMachine(self.session, self.manager.constants.LockType_Shared)

        logging.debug('Lock acquired.')

    def release_lock(self):
        logging.debug('Releasing lock...')

        try:
            self.session.unlockMachine()
        except Exception as e:
            pass

        # Give it a moment to release the lock
        sleep(.5)

        logging.debug('Lock released.')

    def is_running(self):
        logging.debug('Checking if machine is running...')

        if self.machine.state < self.manager.constants.MachineState_FirstOnline:
            logging.debug('Machine is not running.')
            return False

        if self.machine.state > self.manager.constants.MachineState_LastOnline:
            logging.debug('Machine is not running.')
            return False

        logging.debug('Machine is running.')
        return True

    def create(self, name):
        logging.debug('Creating machine...')

        # TODO: Ubuntu should not be hard-coded.
        # This metadata is apparently available in the base dir.
        self.machine = self.vbox.createMachine('', name, [], 'Ubuntu_64', '')

        logging.debug('Registering machine...')
        try:
            self.vbox.registerMachine(self.machine)
        except Exception as e:
            # cleanup any config data that was saved
            logging.debug('Registration failed. Cleaning up config...')
            try:
                progress = self.machine.deleteConfig([])
                progress.waitForCompletion(-1)
            except Exception as e_:
                pass

            raise e

    def clone_from(self, base):
        logging.debug('Creating disk clones...')

        disks = []
        for path in os.listdir(base):
            filename = os.path.join(base, path)
            if not os.path.isfile(filename):
                continue

            if filename.endswith('.vmdk') or filename.endswith('.vdi'):
                disks.append(filename)

        portCount = len(disks)
        storage = self._create_storage(portCount)

        port = 0
        for disk in disks:
            self._create_disk_clone(disk, storage, port)
            port += 1

    def destroy(self):
        logging.debug('Destroying machine...')

        self.stop()

        logging.debug('Unregistering machine...')
        try:
            mediums = self.machine.unregister(
                self.manager.constants.CleanupMode_DetachAllReturnHardDisksOnly
            )
        except Exception as e:
            message = getattr(e, 'msg', e.message)
            raise Exception('Failed to unregister machine: %s' % (message))
        logging.debug('Machine unregistered.')

        logging.debug('Deleting files...')
        try:
            progress = self.machine.deleteConfig(mediums)
            progress.waitForCompletion(-1)
        except Exception as e:
            message = getattr(e, 'msg', e.message)
            raise Exception(
                'Failed to delete files for machine: %s' % (message)
            )
        logging.debug('Files deleted.')

    def start(self, head=False, memory=None, mac=None, ports=None):
        logging.debug('Starting machine...')
        if self.is_running():
            return True

        if self.machine.state != self.manager.constants.MachineState_Saved:
            self._set_boot(memory)
            self._configure_networks(mac)
            self._forward_ports(ports)

        logging.debug('Starting machine...')
        try:
            progress = self.machine.launchVMProcess(
                self.session,
                'gui' if head else 'headless',
                ''
            )
            progress.waitForCompletion(-1)
        except Exception as e:
            # message = getattr(e, 'msg', e.message)
            # raise GenericException(
            #     'Failed to start machine: %s' % (message)
            # )
            raise e
        finally:
            self.release_lock()

    def stop(self):
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
            raise Exception('Failed to shutdown machine: %s' % (message))
        finally:
            self.release_lock()

        logging.debug('Machine stopped.')
        return True

    def _create_storage(self, portCount):
        logging.debug('Creating storage...')

        try:
            self.acquire_lock()

            storage = self.session.machine.addStorageController(
                'SATAController',
                self.manager.constants.StorageBus_SATA
            )
            storage.portCount = portCount
            storage.useHostIOCache = True

            self.session.machine.saveSettings()
        except Exception as e:
            # message = getattr(e, 'msg', e.message)
            # # raise Exception(
            # #     'Unable to create machine storage: %s' % (message)
            # # )
            # click.secho('Error: Unable to create machine storage: %s' % (message), bold=True, fg='red')
            # sys.exit(1)
            raise e
        finally:
            self.release_lock()

        return storage

    def _create_disk_clone(self, filename, storage, port):
        basename = os.path.basename(filename)
        logging.debug('Cloning disk "%s"...' % (basename))

        machine_dir = os.path.dirname(self.machine.settingsFilePath)
        medium_path = os.path.join(machine_dir, basename)

        try:
            self.acquire_lock()

            extension = os.path.splitext(filename)[1].lstrip('.')

            medium = self.vbox.createMedium(
                extension,
                medium_path,
                self.manager.constants.AccessMode_ReadWrite,
                self.manager.constants.DeviceType_HardDisk
            )

            parent = self.vbox.openMedium(
                filename,
                self.manager.constants.DeviceType_HardDisk,
                self.manager.constants.AccessMode_ReadOnly,
                False
            )

            progress = parent.cloneToBase(medium, [self.manager.constants.MediumVariant_Standard])
            progress.waitForCompletion(-1)

            self.session.machine.attachDevice(
                storage.name,
                port,
                0,
                self.manager.constants.DeviceType_HardDisk,
                medium
            )
            self.session.machine.saveSettings()
        except Exception as e:
            logging.debug('Failed to clone disk.')
            if os.path.exists(medium_path):
                logging.debug('Removing medium "%s"...' % (medium_path))
                os.remove(medium_path)

            # message = getattr(e, 'msg', e.message)
            # # raise GenericException(
            # #     'Unable to create machine media: %s' % (message)
            # # )
            # click.secho('Error: Unable to create machine media: %s' % (message), bold=True, fg='red')
            # sys.exit(1)
            raise e
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
            # message = getattr(e, 'msg', e.message)
            # # raise GenericException(
            # #     'Unable to set machine settings: %s' % (message)
            # # )
            # click.secho('Error: Unable to set machine settings: %s' % (message), bold=True, fg='red')
            # sys.exit(1)
            raise e
        finally:
            self.release_lock()

    def _configure_networks(self, nat_mac):
        logging.debug('Configuring network(s)...')
        try:
            self.acquire_lock()

            networkA = self.session.machine.getNetworkAdapter(0)
            networkA.attachmentType = self.manager.constants.NetworkAttachmentType_NAT
            networkA.enabled = True
            networkA.cableConnected = True
            if nat_mac:
                networkA.MACAddress = nat_mac

            # TODO: vboxnet0 needs to be looked up, not assumed
            # networkB = self.session.machine.getNetworkAdapter(1)
            # networkB.attachmentType = self.manager.constants.NetworkAttachmentType_HostOnly
            # networkB.enabled = True
            # networkB.cableConnected = True
            # # networkB.MACAddress =
            # networkB.hostOnlyInterface = "vboxnet0"

            self.session.machine.saveSettings()
        except Exception as e:
            # message = getattr(e, 'msg', e.message)
            # raise GenericException(
            #     'Failed to configure network: %s' % (message)
            # )
            raise e
        finally:
            self.release_lock()

    def _forward_ports(self, ports):
        if ports is None:
            return

        orig_list = self._parse_ports(ports)
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
                    '%d:%d:%s' % (ports['host'], ports['guest'], ports['protocol']),
                    ports['protocol_id'],
                    '127.0.0.1',
                    ports['host'],
                    '',
                    ports['guest']
                )

            self.session.machine.saveSettings()
        except Exception as e:
            # message = getattr(e, 'msg', e.message)
            # raise GenericException(
            #     'Failed to forward ports: %s' % (message)
            # )
            raise e
        finally:
            self.release_lock()

    def _merge_ports(self, ports):
        return ','.join(
            ['%s:%s:%s' % (port['host'], port['guest'], port.get('protocol', 'tcp')) for port in ports]
        )

    def _parse_ports(self, ports):
        port_list = []
        if ports == '':
            return []

        allowed_protocols = {
            'tcp': self.manager.constants.NATProtocol_TCP,
            'udp': self.manager.constants.NATProtocol_UDP
        }

        parts = ports.split(',')
        for part in parts:
            pieces = part.split(':')
            host_port = None
            guest_port = None
            protocol = 'tcp'
            count = len(pieces)
            if 2 > count:
                raise Exception(
                    'Value "%s" is invalid. Expected <host-port>:<guest-port>[:<protocol>]' % (part)
                )

            error = 'Host port "%s" is invalid; must be a number 1-65535.' % (pieces[0])

            try:
                host_port = int(pieces[0])
            except Exception as e:
                raise Exception(error)

            if 0 >= host_port or host_port > 65535:
                raise Exception(error)

            error = 'Guest port "%s" is invalid; must be a number 1-65535.' % (pieces[1])
            try:
                guest_port = int(pieces[1])
            except Exception as e:
                raise Exception(error)

            if 0 >= guest_port or guest_port > 65535:
                raise Exception(error)

            if count >= 3:
                protocol = pieces[2].lower()
                if protocol not in allowed_protocols:
                    raise Exception(
                        'Protocol "%s" is invalid; must be one of ["%s"]' % (
                            protocol,
                            '", "'.join(keys(allowed_protocols))
                        )
                    )

            port_list.append({
                'host': host_port,
                'guest': guest_port,
                'protocol': protocol,
                'protocol_id': allowed_protocols[protocol],
            })

        return port_list

    def _get_collision_free_ports(self, port_list):
        for port in port_list:
            port['host'] = self._get_collision_free_port(port['host'])

        return port_list

    def _get_collision_free_port(self, port):
        # TODO: Fix this.
        return port

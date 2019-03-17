"""Automatically rsync files to a machine."""
from __future__ import absolute_import, division, print_function

import os
from fnmatch import fnmatch
from threading import BoundedSemaphore, Thread
from time import sleep

import click

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import drifter.commands
import drifter.commands.rsync as base_rsync
import drifter.commands.ssh as base_ssh
from drifter.exceptions import GenericException
from drifter.providers import invoke_provider_context


@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
})
@drifter.commands.name_argument
@drifter.commands.command_option
@drifter.commands.pass_config
@click.pass_context
def rsync_auto(ctx, config, name, command):
    """Automatically rsync files to a machine."""
    if not name:
        machines = config.list_machines()
        if machines:
            name = machines.pop()
        if not name:
            raise GenericException('No machines available.')

    provider = config.get_provider(name)
    invoke_provider_context(ctx, provider, [name, '-c', command] + ctx.args)


class RsyncHandler(FileSystemEventHandler):
    """Class to handle rsync events."""

    def __init__(self, config, servers, **kwargs):
        """Set up the handler."""
        super(RsyncHandler, self).__init__()
        self.config = config
        self.servers = servers
        self.kwargs = kwargs
        self.files = {}
        self.included = self._build_list('rsync.include')
        self.excluded = self._build_list('rsync.exclude')
        self.semaphore = BoundedSemaphore()

    def process(self, event):
        """Process the event."""
        Thread(target=self.delay_rsync, args=(event,)).start()

    def on_any_event(self, event):
        """Process all events."""
        self.process(event)

    def delay_rsync(self, event):
        """Delay the rsync to allow for multiple simultaneous saves."""
        local_path = self.kwargs['local_path']
        remote_path = self.kwargs['remote_path']

        relative_path = event.src_path.strip()
        if relative_path.startswith(local_path):
            relative_path = relative_path[len(local_path):]
        else:
            return False

        if self._is_excluded(relative_path):
            return False

        self.files[os.path.join(remote_path, relative_path)] = True

        if not self.semaphore.acquire(blocking=False):
            return False

        sleep(.25)

        has_command = False
        if self.kwargs['command'] or self.kwargs['run_once']:
            has_command = True

        burst_mode = False
        if not has_command:
            click.secho('Rsyncing folder: {0} => {1}'.format(local_path, remote_path), bold=True)
        elif self.kwargs['burst_limit'] > 1 and len(self.files) >= self.kwargs['burst_limit']:
            click.secho('Burst limit exceeded; ignoring rsync', bold=True)
            self.files = {}
            burst_mode = True

        if not burst_mode:
            filelist = list(self.files.keys())
            self.files = {}
            base_rsync.rsync_connect(self.config, self.servers, filelist=filelist,
                                     verbose=not has_command, **self.kwargs)

            if not has_command:
                _show_monitoring_message(self.config)

        self.semaphore.release()

        return True

    def _build_list(self, source):
        patterns = []
        for pattern in self.config.get_default(source, []):
            if pattern[-1] == os.sep:
                pattern += '*'
            patterns.append(pattern)

        return patterns

    def _is_excluded(self, relative_path):
        for include in self.included:
            if fnmatch(relative_path, include):
                return False

        for exclude in self.excluded:
            if fnmatch(relative_path, exclude):
                return True

        return False


def rsync_auto_connect(config, servers, additional_args=[], command=None, run_once=False,
                       burst_limit=0, verbose=True, local_path=None, remote_path=None):
    """Launch rsync-auto for providers."""
    local_path = base_rsync._get_local_path(config, local_path)
    remote_path = base_rsync._get_remote_path(config, remote_path)

    click.secho('Doing an initial rsync...', bold=True)
    base_rsync.rsync_connect(config, servers, additional_args=additional_args,
                             verbose=verbose, local_path=local_path, remote_path=remote_path)

    if command and run_once:
        click.secho('Launching run-once command...', bold=True)

        for server in servers:
            Thread(
                target=base_ssh.ssh_connect,
                args=(config, [server]),
                kwargs={
                    'command': command,
                },
            ).start()

        command = None

    _show_monitoring_message(config)

    handler = RsyncHandler(config, servers, additional_args=additional_args, command=command,
                           burst_limit=burst_limit, run_once=run_once,
                           local_path=local_path, remote_path=remote_path)
    observer = Observer()
    observer.schedule(handler, path=local_path, recursive=True)
    observer.start()

    try:
        while observer.is_alive():
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


def _show_monitoring_message(config):
    message = 'Monitoring files for changes'

    include_list = config.get_default('rsync.include', [])
    if include_list:
        message += '; including [ "{0}" ]'.format(
            '", "'.join(include_list),
        )

    exclude_list = config.get_default('rsync.exclude', [])
    if exclude_list:
        message += '; excluding [ "{0}" ]'.format(
            '", "'.join(exclude_list),
        )

    click.secho(message, bold=True)

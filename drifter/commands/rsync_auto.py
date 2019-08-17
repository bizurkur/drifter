"""Automatically rsync files to a machine."""
from __future__ import absolute_import, division, print_function

import logging
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
from drifter.providers import invoke_provider_context


@click.command(context_settings={
    'ignore_unknown_options': True,
    'allow_extra_args': True,
})
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.command_option
@drifter.commands.pass_config
@click.pass_context
def rsync_auto(ctx, config, name, command):
    """Automatically rsync files to a machine."""
    name = drifter.commands.validate_name(ctx, name)

    if not name:
        machines = drifter.commands.list_machines(config)
        name = machines.pop()

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

        if not self._is_burst(has_command, local_path, remote_path):
            filelist = list(self.files.keys())
            self.files = {}
            kwargs = self.kwargs.copy()
            if has_command:
                if kwargs['verbose']:
                    kwargs['ssh_verbose'] = True
                kwargs['verbose'] = False
            base_rsync.do_rsync(self.config, self.servers, filelist=filelist, **kwargs)

            if not has_command:
                _show_monitoring_message(self.config)

        self.semaphore.release()

        return True

    def _is_burst(self, has_command, local_path, remote_path):
        if self.kwargs['burst_limit'] > 1 and len(self.files) >= self.kwargs['burst_limit']:
            logging.info(click.style('Burst limit exceeded; ignoring rsync', bold=True))
            self.files = {}
            return True

        if not has_command:
            logging.info(
                click.style('Rsyncing folder: %s => %s', bold=True),
                local_path,
                remote_path,
            )

        return False

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


def do_rsync_auto(config, servers, additional_args=None, command=None, run_once=False,
                  burst_limit=0, verbose=True, local_path=None, remote_path=None):
    """Launch rsync-auto for providers."""
    local_path = base_rsync.get_local_path(config, local_path)
    remote_path = base_rsync.get_remote_path(config, remote_path)

    logging.info(click.style('Doing an initial rsync...', bold=True))
    base_rsync.do_rsync(config, servers, additional_args=additional_args,
                        verbose=verbose, local_path=local_path, remote_path=remote_path)

    if command and run_once:
        logging.info(click.style('Launching run-once command...', bold=True))

        for server in servers:
            Thread(
                target=base_ssh.do_ssh,
                args=(config, [server]),
                kwargs={
                    'command': command,
                    'verbose': verbose,
                },
            ).start()

        command = None

    _show_monitoring_message(config)

    handler = RsyncHandler(config, servers, additional_args=additional_args, command=command,
                           burst_limit=burst_limit, run_once=run_once, verbose=verbose,
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

    logging.info(click.style(message, bold=True))

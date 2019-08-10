# Drifter

[![Build Status](https://travis-ci.org/bizurkur/drifter.svg?branch=master)](https://travis-ci.org/bizurkur/drifter)
![pylint Score](https://mperlet.github.io/pybadge/badges/10.svg)

Easy and dynamic machine creation.

**This is a work in progress.** Drifter is very similar to the concept of [Vagrant](https://www.vagrantup.com/) - it builds machines from different providers on the fly and allows you to interact with them.

The only provider at this time that is being worked on is [VirtualBox](https://www.virtualbox.org/). However, once that's done work *could* be done to expand and support other providers like [Amazon Web Services](https://aws.amazon.com/), [Google Cloud Platform](https://cloud.google.com/), and maybe even [Microsoft Azure](https://azure.microsoft.com/). It all depends on how bored I get.

This is not intended as a 1-to-1 replacement for Vagrant. This is not a port from Ruby to Python. I have no intention of creating every command or option Vagrant supports. If you want all that, then use Vagrant. This will start out only supporting (what I deem as) the essential commands and options. Further support can be added later on, if needed.

## Why make it?

Vagrant is awesome and already does this - so why bother? On my computer Vagrant runs extremely slow - we're talking 30+ seconds to *start* a command. I don't know why it's so slow (maybe it's my computer), but the speed is not satisfactory to me. It hinders my ability to get work done and I don't like waiting forever to rsync something as simple as a single-line CSS change.

- [Installation](#installation)
- [Usage](#usage)
- [Commands](#commands)
- [Providers](#providers)
- [Plugins](#plugins)
- [Creating a Base Machine](#creating-a-base-machine)
- [Autocompletion](#autocompletion)


# Installation

```sh
$ sudo -E python setup.py install
```

# Usage

To use it:

```sh
$ drifter
```

More docs will be added as commands get completed.


----

# Commands

Most, if not all, commands at the base level will be aliases for commands at the provider level. This means when you run `drifter up` that it is internally forwarding the command to `drifter <provider> up`. Since each provider can have different options it accepts, the base commands have a simplified help section. To view the full details of what options are available, you'd have to run `drifter <provider> <command> --help`.

With the exception of the `up` command, all other commands automatically detect which provider to use based on the machine name given.

- [destroy](#destroy-command)
- [halt](#halt-command)
- [help](#help-command)
- [list](#list-command)
- [provision](#provision-command)
- [rsync](#rsync-command)
- [rsync-auto](#rsync-auto-command)
- [ssh](#ssh-command)
- [status](#status-command)
- [up](#up-command)


## `destroy` Command

The `destroy` command shuts down a machine and removes all traces of its existence. You will be given a prompt for confirmation, as this action cannot be undone.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to destroy.

### Options

#### `--force`, `-f`

The `--force` option allows you to bypass the confirmation prompt and go straight to destroying the machine.

#### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

#### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


## `halt` Command

The `halt` command shuts down a machine, but maintains all of its settings and files.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to halt.

### Options

#### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

#### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


## `help` Command

The `help` command prints out the available commands and providers, as well as version information.


## `list` Command

The `list` command lists all available machines, including both running and halted machines.

### Options

#### `--select`

The `--select` option allows you to set a default machine to use for commands. You can select a machine using its name or the number shown next to it, e.g. `--select foobar` or `--select 1`.

When a machine is selected, an indicator (`*`) will be printed next to it.

You can also set a default machine by setting an environmental variable, e.g. `export DRIFTER_NAME='foobar'`.

#### `--no-select`

The `--no-select` option unsets the selected machine. However, it will not unset the `DRIFTER_NAME` environmental variable.

#### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

#### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


## `provision` Command

The `provision` command provisions a machine for use. This can include copying files, running programs, or executing scripts.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to provision.

### Options

#### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

#### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.

### Provisioners

#### `rsync`

The `rsync` provisioner copies files to the machine. Multiple rsync provisioners can be set up to sync different local paths to different remote paths.

TODO: Finish this.

#### `shell`

The `shell` provisioner executes programs or scripts.

TODO: Finish this.

## `rsync` Command

The `rsync` command remotely syncs files to a machine over SSH.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to connect to.

### Options

#### `--command`, `-c`

The `--command` option allows you to execute a command remotely after the rsync is complete. This can be very useful for many things, such as compiling web assets after a change is made to some CSS or JS.

#### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

#### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


## `rsync-auto` Command

The `rsync-auto` command remotely syncs files to a machine over SSH (exactly like the `rsync` command does), but it does it automatically when a file changes.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to connect to.

### Options

#### `--command`, `-c`

The `--command` option allows you to execute a command remotely after the rsync is complete. This can be very useful for many things, such as compiling web assets after a change is made to some CSS or JS.

#### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

#### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


## `ssh` Command

The `ssh` command opens a secure shell (SSH) connection to a machine.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to connect to.

### Options

#### `--command`, `-c`

The `--command` option allows you to execute a command remotely without opening a full connection in your terminal. For example, `drifter ssh -c 'ls -al'` will display a list of files on the remote machine and then return your terminal to the current working directory.

#### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

#### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


## `status` Command

The `status` command gets the status and some basic metadata for a machine. This includes printing its name, provider, and other information that may vary by provider.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to get the status for.

### Options

#### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

#### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


## `up` Command

The `up` command brings machines up and gets them running. This may involve creating the machine if it doesn't exist or may simply require starting it if it is in a stopped state. This is typically the first command you will need to run.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to bring up.

### Options

#### `--provider`

The `--provider` option allows for specifying which provider to create the machine in. By default, the provider will be VirtualBox. You can override this by either setting a `provider` value in the config or by setting a `DRIFTER_PROVIDER` environment variable.

```sh
# For one-time usage
DRIFTER_PROVIDER='foobar' drifter up

# Or, set it and forget it
export DRIFTER_PROVIDER='foobar'
drifter up
```

#### `--provision`, `--no-provision`

The `--provision` and `--no-provision` options determine whether or not to provision the machine after it comes up. By default, it will only provision a machine if it hasn't already been provisioned.

#### `--provision-with`

The `--provision-with` option allows you to limit a specific provisioner name or type to be ran. For example, `--provision-with rsync` will only run rsync provisioners.

#### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

#### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.

----

# Providers

- [VirtualBox](#virtualbox)
- [Make Your Own](#make-your-own)

## VirtualBox

[VirtualBox](https://www.virtualbox.org/) is a free download and allows for creating virtual machines at a local level.

- [destroy](#destroy-command-1)
- [halt](#halt-command-1)
- [provision](#provision-command-1)
- [rsync](#rsync-command-1)
- [rsync-auto](#rsync-auto-command-1)
- [ssh](#ssh-command-1)
- [status](#status-command-1)
- [up](#up-command-1)


### `destroy` Command

The `destroy` command shuts down a machine and removes all traces of its existence. You will be given a prompt for confirmation, as this action cannot be undone.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to destroy.

#### Options

##### `--force`, `-f`

The `--force` option allows you to bypass the confirmation prompt and go straight to destroying the machine.

##### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

##### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


### `halt` Command

The `halt` command shuts down a machine, but maintains all of its settings and files.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to halt.

#### Options

##### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

##### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


### `provision` Command

The `provision` command provisions a machine for use. This can include copying files, running programs, or executing scripts.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to provision.

#### Options

##### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

##### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


### `rsync` Command

The `rsync` command remotely syncs files to a machine over SSH.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to connect to.

#### Options

##### `--command`, `-c`

The `--command` option allows you to execute a command remotely after the rsync is complete. This can be very useful for many things, such as compiling web assets after a change is made to some CSS or JS.

##### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

##### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.

#### Additional Options

This command allows for a direct interaction with the underlying system command and any argument or option can be passed to it. To pass in direct options, simply add a `--` (double hyphen) argument followed by whatever you want to pass in. For example, if you wanted to exclude an additional file, you would do `drifter rsync -- --exclude some.file`.


### `rsync-auto` Command

The `rsync-auto` command remotely syncs files to a machine over SSH (exactly like the `rsync` command does), but it does it automatically when a file changes.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to connect to.

#### Options

##### `--burst-limit`

The `--burst-limit` option prevents doing an rsync when a burst of files all change at the same time, e.g. when switching between git branches. Sometimes mass file changes can cause undesired effects and this is a way to prevent that. By default, the limit is `0` (disabled).

It's worth noting that when a file changes, it may also trigger other events. All of those events are considered when determining if a "burst" happened. For example, saving a single file may trigger all of the following events: file change event, directory change event, and a lock file change event. Even though only one file was changed, a burst of three events would be seen. If `--burst-limit 2` was specified, the rsync would be ignored.

##### `--command`, `-c`

The `--command` option allows you to execute a command remotely after the rsync is complete. This can be very useful for many things, such as compiling web assets after a change is made to some CSS or JS.

The command can contain a `{}` placeholder to represent the file path(s) being rsynced, e.g. `drifter rsync-auto -c 'echo {}'` will echo the file paths that have changed.

##### `--run-once`

The `--run-once` option signals to only execute the `--command` option once. This is useful when the command specified runs continuously, so there's no need to start multiple instances of the command.

##### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

##### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.

#### Additional Options

This command allows for a direct interaction with the underlying system command and any argument or option can be passed to it. To pass in direct options, simply add a `--` (double hyphen) argument followed by whatever you want to pass in. For example, if you wanted to exclude an additional file, you would do `drifter rsync-auto -- --exclude some.file`.


### `ssh` Command

The `ssh` command opens a secure shell (SSH) connection to a machine.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to connect to.

#### Options

##### `--command`, `-c`

The `--command` option allows you to execute a command remotely without opening a full connection in your terminal. For example, `drifter ssh -c 'ls -al'` will display a list of files on the remote machine and then return your terminal to the current working directory.

##### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

##### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.

#### Additional Options

This command allows for a direct interaction with the underlying system command and any argument or option can be passed to it. To pass in direct options, simply add a `--` (double hyphen) argument followed by whatever you want to pass in. For example, if you wanted to forward the authentication agent connection, you would do `drifter ssh -- -A`. Or if you wanted to see the verbose connection details, `drifter ssh -- -vvv`.


### `status` Command

The `status` command gets the status and some basic metadata for a machine. This includes printing its name, provider, and any forwarded ports.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to get the status for.

#### Options

##### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

##### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


### `up` Command

The `up` command brings machines up and gets them running. This may involve creating the machine if it doesn't exist or may simply require starting it if it is in a stopped state. This is typically the first command you will need to run.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to bring up.

#### Options

##### `--provision`, `--no-provision`

The `--provision` and `--no-provision` options determine whether or not to provision the machine after it comes up. By default, it will only provision a machine if it hasn't already been provisioned.

##### `--provision-with`

The `--provision-with` option allows you to limit a specific provisioner name or type to be ran. For example, `--provision-with rsync` will only run rsync provisioners.

##### `--base`

The `--base` option allows for specifying which machine to import as the base. For now, this expects to be given a full path to the directory of an existing virtual machine. The base machine should include the operating system and any other required software. See the "Creating a Base Machine" section for more details.

##### `--head`, `--no-head`

The `--head` and `--no-head` options control whether or not to run the machine with a head; or, in simplified terms, whether to run it in a visible window or not. The default is `--no-head`, making the machine run in the background. If you specify `--head` the machine will start up with a visible window that you can interact with. This might come in handy for certain debugging activities.

##### `--mac`

The `--mac` option allows for customizing the Media Access Control (MAC) address of the Network Address Translation (NAT) interface assigned to the machine.

##### `--memory`

The `--memory` option allows for specifying how much memory the machine should be given. This should be an integer in megabytes, e.g. `1024` means to use 1024MB (1GB) of RAM. It will default to a minimum of 512MB.

##### `--ports`

The `--ports` option allows for forwarding specific ports from the host machine to the guest machine. This is a string in the format of `<host>:<guest>[:<protocol>]` where `<host>` is the host port, `<guest>` is the guest port, and `<protocol>` is `tcp` or `udp`. If `<protocol>` is not provided, `tcp` is assumed.

You can also specify multiple ports to forward by separating each string with a comma. For example, if you wanted to forward connections for both HTTP and SSH, you would do something like `--ports 8080:80,2222:22`. That would forward all connections to `localhost:8080` to the guest machine's port 80 and connections to `localhost:2222` to the guest machine's port 22.

##### `--quiet`, `-q`

The `--quiet` option decreases the verbosity of the command. Multiple instances of this option are supported. Each instance will decrease the verbosity by 1, e.g. `-qqq` will decrease the verbosity by 3.

##### `--verbose`, `-v`

The `--verbose` option increases the verbosity of the command. Multiple instances of this option are supported. Each instance will increase the verbosity by 1, e.g. `-vvv` will increase the verbosity by 3.


## Make Your Own

To create your own provider, add your provider to the entry point `drifter.providers` in your `setup.py`.

```python
from setuptools import setup

setup(
    name='test_provider',
    version='0.1',
    packages=['test_provider'],
    install_requires=[
        'click',
    ],
    entry_points='''
        [drifter.providers]
        my-provider=test_provider:my_provider
    ''',
)
```

Then make sure to tag the main method (in this case `my_provider`) as a [Click](https://click.palletsprojects.com/) command group.

```python
# test_provider/__init__.py
"""Example provider that does nothing."""

import click

import drifter.commands

@click.group(invoke_without_command=True)
@click.pass_context
def my_provider(ctx):
    """Example provider."""
    if not ctx.invoked_subcommand:
        click.echo(ctx.get_help())


@my_provider.command()
@drifter.commands.name_argument
@drifter.commands.verbosity_options
@drifter.commands.provision_option
@drifter.commands.pass_config
def up(config, name, provision):
    print('Do stuff')
```

See the [full example provider](examples/providers/) for more context.

----

# Plugins

Drifter supports creating plugins for adding any additional commands you may need.

## Creating a Plugin

To create a plugin, add your sub-commands or sub-groups to the entry point `drifter.plugins` in your `setup.py`.

```python
from setuptools import setup

setup(
    name='test_plugin',
    version='0.1',
    packages=['test_plugin'],
    install_requires=[
        'click',
    ],
    entry_points='''
        [drifter.plugins]
        foo=test_plugin:foo
        bar=test_plugin:bar
    ''',
)
```

Then make sure to tag the methods as [Click](https://click.palletsprojects.com/) commands.

```python
# test_plugin/__init__.py
"""Example plugin that does nothing."""

import click

@click.command()
def foo():
    """This is foo"""
    print('You called foo')

@click.command()
def bar():
    """This is bar"""
    print('You called bar')
```

See the [example plugins](examples/plugins/) for more context.

----

# Creating a Base Machine

The base machine should create a `drifter` user and set up the default [SSH keys](https://github.com/bizurkur/drifter/tree/master/keys).

TODO: Add more to this later.


# Autocompletion

To enable Bash autocompletion:

    $ _DRIFTER_COMPLETE=source drifter > ~/drifter-complete.sh

Then add this line to your .bashrc or .bash_profile file:

    . ~/drifter-complete.sh

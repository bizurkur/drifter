# Drifter

[![Build Status](https://travis-ci.org/bizurkur/drifter.svg?branch=master)](https://travis-ci.org/bizurkur/drifter)

Easy and dynamic machine creation.

**This is a work in progress.** Drifter is very similar to the concept of [Vagrant](https://www.vagrantup.com/) - it builds machines from different providers on the fly and allows you to interact with them.

The only provider at this time that is being worked on is [VirtualBox](https://www.virtualbox.org/). However, once that's done work *could* be done to expand and support other providers like [Amazon Web Services](https://aws.amazon.com/), [Google Cloud Platform](https://cloud.google.com/), and maybe even [Microsoft Azure](https://azure.microsoft.com/). It all depends on how bored I get.

This is not intended as a 1-to-1 replacement for Vagrant. This is not a port from Ruby to Python. I have no intention of creating every command or option Vagrant supports. If you want all that, then use Vagrant. This will start out only supporting (what I deem as) the essential commands and options. Further support can be added later on, if needed.

## Why make it?

Vagrant is awesome and already does this - so why bother? On my computer Vagrant runs extremely slow - we're talking 30 seconds to a full minute just to *start* a command. I suspect it's so slow because Vagrant communicates to VirtualBox directly through the CLI. I believe this is a decision Vagrant made years ago for wider compatibility across different operating systems, but not 100% sure. It's also possible it's my computer that is the bottleneck. Regardless as to why it's slow, the speed is not satisfactory to me. It hinders my ability to get work done and I don't like waiting forever to rsync something as simple as a single-line CSS change.

I found out VirtualBox provides a Python SDK for interacting with VirtualBox over XPCOM. So I started tinkering with it. I quickly realized how much faster it was and decided to make my own tool.


# Installation

## Install VirtualBox SDK

First you need to install the VirtualBox Software Developer Kit (SDK), if not already installed. This provides access to the `vboxapi` Python package. To do that:

- Go to the [VirtualBox Downloads](https://www.virtualbox.org/wiki/Downloads) page.
- Click the link for the Software Developer Kit.
- Unzip the file.
- If on MacOS or linux, run:

```sh
$ export VBOX_INSTALL_PATH=/usr/lib/virtualbox
$ sudo -E python vboxapisetup.py install
```

## Install `drifter`

```sh
$ sudo -E python setup.py install
```

# Usage

To use it:

```sh
$ drifter help
```

More docs will be added as commands get completed.


----

# Commands

Most, if not all, commands at the base level will be aliases for commands at the provider level. This means when you run `drifter up` that it is internally forwarding the command to `drifter <provider> up`. Since each provider can have different options it accepts, the base commands have a simplified help section. To view the full details of what options are available, you'd have to run `drifter <provider> <command> --help`.

With the exception of the `up` command, all other commands automatically detect which provider to use based on the machine name given.

- [destroy](#destroy-command)
- [halt](#halt-command)
- [list](#list-command)
- [rsync](#rsync-command)
- [rsync-auto](#rsync-auto-command)
- [ssh](#ssh-command)
- [up](#up-command)

## `destroy` Command

The `destroy` command shuts down a machine and removes all traces of its existence. You will be given a prompt for confirmation, as this action cannot be undone.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to destroy.

### Options

#### `--force`, `-f`

The `--force` option allows you to bypass the confirmation prompt and go straight to destroying the machine.

## `halt` Command

The `halt` command shuts down a machine, but maintains all of its settings and files.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to halt.

## `list` Command

The `list` command lists the available machines, including both started and non-started machines.

### Options

#### `--select`

The `--select` option allows you to set a default machine to use for commands. You can select a machine using its name or the number shown next to it, e.g. `--select foobar` or `--select 1`.

When a machine is selected, an indicator (`*`) will be printed next to it.

You can also set a default machine by setting an environmental variable, e.g. `export DRIFTER_NAME='foobar'`.

#### `--no-select`

The `--no-select` option unsets the selected machine. However, it will not unset the `DRIFTER_NAME` environmental variable.

## `rsync` Command

The `rsync` command remotely syncs files to a machine over SSH.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to connect to.

### Options

#### `--command`, `-c`

The `--command` option allows you to execute a command remotely after the rsync is complete. This can be very useful for many things, such as compiling web assets after a change is made to some CSS or JS.

## `rsync-auto` Command

The `rsync-auto` command remotely syncs files to a machine over SSH (exactly like the `rsync` command does), but it does it automatically when a file changes.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to connect to.

### Options

#### `--command`, `-c`

The `--command` option allows you to execute a command remotely after the rsync is complete. This can be very useful for many things, such as compiling web assets after a change is made to some CSS or JS.

## `ssh` Command

The `ssh` command opens a secure shell (SSH) connection to a machine.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to connect to.

### Options

#### `--command`, `-c`

The `--command` option allows you to execute a command remotely without opening a full connection in your terminal. For example, `-c 'ls -al'` will display a list of files on the remote machine and then return your terminal to the current working directory.

## `up` Command

The `up` command brings machines up and gets them running. This may involve creating the machine if it doesn't exist or may simply require starting it if it is in a stopped state. This is typically the first command you will need to run.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to bring up.

### Options

#### `--provider`

The `--provider` option allows for specifying which provider to create the machine in. By default, the provider will be VirtualBox.

----

# Providers

- [VirtualBox](#virtualbox)

## VirtualBox

[VirtualBox](https://www.virtualbox.org/) is a free download and allows for creating virtual machines at a local level.

- [destroy](#destroy-command-1)
- [halt](#halt-command-1)
- [rsync](#rsync-command-1)
- [rsync-auto](#rsync-auto-command-1)
- [ssh](#ssh-command-1)
- [up](#up-command-1)

### `destroy` Command

The `destroy` command shuts down a machine and removes all traces of its existence. You will be given a prompt for confirmation, as this action cannot be undone.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to destroy.

#### Options

##### `--force`, `-f`

The `--force` option allows you to bypass the confirmation prompt and go straight to destroying the machine.

### `halt` Command

The `halt` command shuts down a machine, but maintains all of its settings and files.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to halt.

### `rsync` Command

The `rsync` command remotely syncs files to a machine over SSH.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to connect to.

#### Options

##### `--command`, `-c`

The `--command` option allows you to execute a command remotely after the rsync is complete. This can be very useful for many things, such as compiling web assets after a change is made to some CSS or JS.

The command can contain a `{}` placeholder to represent the file path(s) being rsynced, e.g. `-c 'echo {}'` will echo the file paths that have changed.

#### Additional Options

This command allows for a direct interaction with the underlying system command and any argument or option can be passed to it. To pass in direct options, simply add a `--` (double hyphen) argument followed by whatever you want to pass in. For example, if you wanted to exclude an additional file, you would do `drifter rsync -- --exclude some.file`.

### `rsync-auto` Command

The `rsync-auto` command remotely syncs files to a machine over SSH (exactly like the `rsync` command does), but it does it automatically when a file changes.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to connect to.

#### Options

##### `--command`, `-c`

The `--command` option allows you to execute a command remotely after the rsync is complete. This can be very useful for many things, such as compiling web assets after a change is made to some CSS or JS.

The command can contain a `{}` placeholder to represent the file path(s) being rsynced, e.g. `-c 'echo {}'` will echo the file paths that have changed.

##### `--run-once`

The `--run-once` option signals to only execute the `--command` option once. This is useful when the command specified runs continuously, so there's no need to start multiple instances of the command.

##### `--burst-limit`

The `--burst-limit` option prevents doing an rsync when a burst of files all change at the same time, e.g. when switching between git branches. Sometimes mass file changes can cause undesired effects and this is a way to prevent that. By default, the limit is `0` (disabled).

It's worth noting that when a file changes, it may also trigger other events. All of those events are considered when determining if a "burst" happened. For example, saving a single file may trigger all of the following events: file change event, directory change event, and a lock file change event. Even though only one file was changed, a burst of three events would be seen. If `--burst-limit 2` was specified, the rsync would be ignored.

#### Additional Options

This command allows for a direct interaction with the underlying system command and any argument or option can be passed to it. To pass in direct options, simply add a `--` (double hyphen) argument followed by whatever you want to pass in. For example, if you wanted to exclude an additional file, you would do `drifter rsync-auto -- --exclude some.file`.

### `ssh` Command

The `ssh` command opens a secure shell (SSH) connection to a machine.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to connect to.

#### Options

##### `--command`, `-c`

The `--command` option allows you to execute a command remotely without opening a full connection in your terminal. For example, `-c 'ls -al'` will display a list of files on the remote machine and then return your terminal to the current working directory.

#### Additional Options

This command allows for a direct interaction with the underlying system command and any argument or option can be passed to it. To pass in direct options, simply add a `--` (double hyphen) argument followed by whatever you want to pass in. For example, if you wanted to forward the authentication agent connection, you would do `drifter ssh -- -A`. Or if you wanted to see the verbose connection details, `drifter ssh -- -vvv`.

### `up` Command

The `up` command brings machines up and gets them running. This may involve creating the machine if it doesn't exist or may simply require starting it if it is in a stopped state. This is typically the first command you will need to run.

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to bring up.

#### Options

##### `--base`

The `--base` option allows for specifying which machine to import as the base. For now, this expects to be given a full path to the directory of an existing virtual machine. The base machine should include the operating system and any other required software. See the "Creating a Base Machine" section for more details.

##### `--memory`

The `--memory` option allows for specifying how much memory the machine should be given. This should be an integer in megabytes, e.g. `1024` means to use 1024MB (1GB) of RAM. It will default to a minimum of 512MB.

##### `--mac`

The `--mac` option allows for customizing the Media Access Control (MAC) address of the Network Address Translation (NAT) interface assigned to the machine.

##### `--ports`

The `--ports` option allows for forwarding specific ports from the host machine to the guest machine. This is a string in the format of `<host>:<guest>[:<protocol>]` where `<host>` is the host port, `<guest>` is the guest port, and `<protocol>` is `tcp` or `udp`. If `<protocol>` is not provided, `tcp` is assumed.

You can also specify multiple ports to forward by separating each string with a comma. For example, if you wanted to forward connections for both HTTP and SSH, you would do something like `--ports 8080:80,2222:22`. That would forward all connections to `localhost:8080` to the guest machine's port 80 and connections to `localhost:2222` to the guest machine's port 22.

##### `--head`, `--no-head`

The `--head` and `--no-head` options control whether or not to run the machine with a head; or, in simplified terms, whether to run it in a visible window or not. The default is `--no-head`, making the machine run in the background. If you specify `--head` the machine will start up with a visible window that you can interact with. This might come in handy for certain debugging activities.

----

# Creating a Base Machine

The base machine should create a `drifter` user and set up the default [SSH keys](https://github.com/bizurkur/drifter/tree/master/keys).

TODO: Add more to this later.


# Autocompletion

To enable Bash autocompletion:

    $ _DRIFTER_COMPLETE=source drifter > ~/drifter-complete.sh

Then add this line to your .bashrc or .bash_profile file:

    . ~/drifter-complete.sh

# Drifter

Easy and dynamic machine creation.

**This is a work in progress.** Drifter is very similar to the concept of [Vagrant](https://www.vagrantup.com/) - it builds machines from different providers on the fly and allows you to interact with them.

The only provider at this time that is being worked on is [VirtualBox](https://www.virtualbox.org/). However, once that's done work *could* be done to expand and support other providers like [Amazon Web Services](https://aws.amazon.com/), [Google Cloud Platform](https://cloud.google.com/), and maybe even [Microsoft Azure](https://azure.microsoft.com/). It all depends on how bored I get.

This is not intended as a 1-to-1 replacement for Vagrant. This is not a port from Ruby to Python. I have no intention of creating every command or option Vagrant supports. If you want all that, then use Vagrant. This will start out only supporting (what I deem as) the essential commands and options. Further support can be added later on, if needed.

## Why make it?

Vagrant is awesome and already does this - so why bother? On my computer Vagrant runs extremely slow - we're talking 30 seconds to a full minute just to *start* a command. I suspect it's so slow because Vagrant communicates to VirtualBox directly through the CLI. I believe this is a decision Vagrant made years ago for wider compatibility across different operating systems, but not 100% sure. Regardless as to why it's slow, the speed is not satisfactory to me. It hinders my ability to get work done and I don't like waiting forever to rsync something as simple as a single-line CSS change.

I found out VirtualBox provides a Python SDK for interacting with VirtualBox over XPCOM. So I started tinkering with it. I quickly realized how much faster it was and decided to make my own tool.


# Installation

If you don't use `pipsi`, you're missing out.
Here are [installation instructions](https://github.com/mitsuhiko/pipsi#readme).

Simply run:

    $ pipsi install .


# Usage

To use it:

    $ drifter help

More docs will be added as commands get completed.


----

# Commands

Most, if not all, commands at the base level will be aliases for commands at the provider level. This means when you run `drifter up` that it is internally forwarding the command to `drifter <provider> up`. Since each provider can have different options it accepts, the base commands have a simplified help section. To view the full details of what options are available, you'd have to run `drifter <provider> <command> --help`.

With the exception of the `up` command, all other commands detect which provider to use automatically.

## `up` Command

The `up` command brings machines up and gets them running. This may involve creating the machine if it doesn't exist or may simply require starting it if it is in a stopped state. This is typically the first command you will need to run.

### Arguments

#### `name`

The `name` argument specifies the name of the machine to bring up.

### Options

#### `--provider`

The `--provider` option allows for specifying which provider to create the machine in. By default, the provider will be VirtualBox.

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

----

# Providers

## VirtualBox

[VirtualBox](https://www.virtualbox.org/) is a free download and allows for creating virtual machines at a local level.

### `up` Command

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

### `destroy` Command

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to destroy.

#### Options

##### `--force`, `-f`

The `--force` option allows you to bypass the confirmation prompt and go straight to destroying the machine.

### `halt` Command

#### Arguments

##### `name`

The `name` argument specifies the name of the machine to halt.

----

# Creating a Base Machine

The base machine should create a `drifter` user and set up the default SSH keys.

TODO: Add more to this later.


# Autocompletion

To enable Bash autocompletion:

    $ _DRIFTER_COMPLETE=source drifter > drifter-complete.sh

Then add this line to your .bashrc file:

    . /path/to/drifter-complete.sh

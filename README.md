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

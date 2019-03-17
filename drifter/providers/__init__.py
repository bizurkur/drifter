"""Shared provider functions."""
from __future__ import absolute_import, division, print_function

import os
from functools import update_wrapper

import click

from drifter.exceptions import ProviderException


def pass_provider(f):
    """Pass the provider object into a command."""
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        return ctx.invoke(f, ctx.obj['provider'], *args, **kwargs)

    return update_wrapper(new_func, f)


def get_providers():
    """Get a list of available providers."""
    providers = []
    folder = os.path.dirname(__file__)
    for provider in os.listdir(folder):
        provider_folder = os.path.join(folder, provider)
        init = os.path.join(folder, provider, '__init__.py')
        if os.path.isdir(provider_folder) and os.path.exists(init):
            providers.append(provider)

    providers.sort()

    return providers


def get_provider(provider):
    """Get the given provider module."""
    try:
        module = __import__('drifter.providers.{0}'.format(provider), fromlist=['drifter.providers'])
    except ImportError as e:
        raise ProviderException(
            'Provider "%s" is invalid: {0}'.format(provider, e.message),
        )

    cmd = getattr(module, provider, None)
    if not cmd:
        raise ProviderException(
            'Provider "{0}" does not define a subcommand.'.format(provider),
        )

    if not isinstance(cmd, click.core.Group):
        raise ProviderException(
            'Provider "{0}" is not set up as a command group.'.format(provider),
        )

    return cmd


def make_provider_context(ctx, provider, args):
    """Make a provider context."""
    sub_ctx = get_provider(provider).make_context(
        provider,
        [ctx.info_name] + args,
        parent=ctx.parent,
    )

    return sub_ctx


def invoke_provider_context(ctx, provider, args):
    """Make a provider context and invoke it."""
    sub_ctx = make_provider_context(ctx, provider, args)
    with sub_ctx:
        sub_ctx.command.invoke(sub_ctx)

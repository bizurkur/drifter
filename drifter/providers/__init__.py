"""Shared provider functions."""
from __future__ import absolute_import, division, print_function

from functools import update_wrapper

import click

from pkg_resources import iter_entry_points

from drifter.exceptions import ProviderException


DEFAULT_PROVIDER = 'virtualbox'


def pass_provider(func):
    """Pass the provider object into a command."""
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        """Invoke the function, adding the provider argument."""
        return ctx.invoke(func, ctx.obj['provider'], *args, **kwargs)

    return update_wrapper(new_func, func)


def get_providers():
    """Get a list of available providers."""
    providers = {}
    for entry_point in iter_entry_points('drifter.providers'):
        providers[entry_point.name] = entry_point

    return providers


def get_provider(provider):
    """Get the given provider module."""
    providers = get_providers()

    clean_name = provider.replace('-', '_')
    if clean_name in providers:
        cmd = providers[clean_name].load()
    elif provider in providers:
        cmd = providers[provider].load()
    else:
        raise ProviderException('Provider "{0}" is invalid'.format(provider))

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

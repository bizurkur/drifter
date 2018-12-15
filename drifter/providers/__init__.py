from __future__ import print_function, absolute_import, division
from functools import update_wrapper
import os

import click

from drifter.exceptions import ProviderException

def pass_provider(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        return ctx.invoke(f, ctx.obj['provider'], *args, **kwargs)

    return update_wrapper(new_func, f)

def get_providers():
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
    try:
        module = __import__('drifter.providers.%s' % (provider), fromlist=['drifter.providers'])
    except ImportError as e:
        raise ProviderException(
            'Provider "%s" is invalid: %s' % (provider, e.message)
        )

    cmd = getattr(module, provider, None)
    if not cmd:
        raise ProviderException(
            'Provider "%s" does not define a subcommand.' % (provider)
        )

    if not isinstance(cmd, click.core.Group):
        raise ProviderException(
            'Provider "%s" is not set up as a command group.' % (provider)
        )

    return cmd

def get_provider_cmd(ctx, provider, name):
    provider_cmd = get_provider(provider)

    cmd = provider_cmd.get_command(ctx, name)
    if not cmd:
        raise ProviderException(
            'Provider "%s" does not have a "%s" command.' % (provider, name)
        )

    return cmd

def make_provider_context(ctx, provider, args):
    sub_ctx = get_provider(provider).make_context(
        provider,
        [ctx.info_name] + args,
        parent=ctx.parent
    )

    return sub_ctx

def invoke_provider_context(ctx, provider, args):
    sub_ctx = make_provider_context(ctx, provider, args)
    with sub_ctx:
        sub_ctx.command.invoke(sub_ctx)

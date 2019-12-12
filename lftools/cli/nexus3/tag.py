import logging
from pprint import pformat

import click


log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def tag(ctx):
    pass


@tag.command(name="add")
@click.argument("name")
@click.argument("attributes", required=False)
@click.pass_context
def add_tag(ctx, name, attributes):
    r = ctx.obj["nexus"]
    data = r.create_tag(name, attributes)
    log.info(pformat(data))


@tag.command(name="delete")
@click.argument("name")
@click.pass_context
def delete_tag(ctx, name):
    r = ctx.obj["nexus"]
    data = r.delete_tag(name)
    log.info(pformat(data))


@tag.command(name="list")
@click.pass_context
def list_tags(ctx):
    r = ctx.obj["nexus"]
    data = r.list_tags()
    log.info(pformat(data))


@tag.command(name="show")
@click.argument("name")
@click.pass_context
def show_tag(ctx, name):
    r = ctx.obj["nexus"]
    data = r.show_tag(name)
    log.info(pformat(data))

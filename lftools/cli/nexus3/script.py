import logging
from lftools.api.endpoints import nexus  # noqa: F401

import click

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def script(ctx):
    pass


@script.command(name="create")
@click.argument("name")
@click.argument("filename")
@click.pass_context
def create_script(ctx, name, filename):
    r = ctx.obj["nexus"]
    data = r.create_script(name, filename)
    log.info(data)


@script.command(name="delete")
@click.argument("name")
@click.pass_context
def delete_script(ctx, name):
    r = ctx.obj["nexus"]
    data = r.delete_script(name)
    log.info(data)


@script.command(name="list")
@click.pass_context
def list_scripts(ctx):
    r = ctx.obj["nexus"]
    data = r.list_scripts()
    log.info(data)


@script.command(name="read")
@click.argument("name")
@click.pass_context
def read_script(ctx, name):
    r = ctx.obj["nexus"]
    data = r.read_script(name)
    log.info(data)


@script.command(name="run")
@click.argument("name")
@click.pass_context
def run_script(ctx, name):
    r = ctx.obj["nexus"]
    data = r.run_script(name)
    log.info(data)


@script.command(name="update")
@click.argument("name")
@click.argument("content")
@click.pass_context
def update_script(ctx, name, content):
    r = ctx.obj["nexus"]
    data = r.update_script(name, content)
    log.info(data)

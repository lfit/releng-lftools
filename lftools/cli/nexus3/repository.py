import click
import logging
from pprint import pformat
from lftools.api.endpoints import nexus  # noqa: F401


log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def repository(ctx):
    pass


@repository.command(name="list")
@click.pass_context
def list_repositories(ctx):
    r = ctx.obj["nexus"]
    data = r.list_repositories()
    log.info(pformat(data))

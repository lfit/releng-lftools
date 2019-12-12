import click
import logging
from pprint import pformat
from lftools.api.endpoints import nexus


log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def asset(ctx):
    pass


@asset.command(name="list")
@click.argument("repository")
@click.pass_context
def asset_list(ctx, repository):
    r = ctx.obj["nexus"]
    data = r.list_assets(repository)
    for item in data:
        log.info(pformat(item))


@asset.command(name="search")
@click.argument("query-string")
@click.argument("repository")
@click.option("--details", is_flag=True)
@click.pass_context
def asset_search(ctx, query_string, repository, details):
    r = ctx.obj["nexus"]
    data = r.search_asset(query_string, repository, details)

    if details:
        log.info(data)
    else:
        for item in data:
            log.info(item)

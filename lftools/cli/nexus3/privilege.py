import logging
from tabulate import tabulate

import click


log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def privilege(ctx):
    pass


@privilege.command(name="list")
@click.pass_context
def list_privileges(ctx):
    r = ctx.obj["nexus"]
    data = r.list_privileges()
    log.info(
        tabulate(data, headers=["Type", "Name", "Description", "Read Only"])
    )

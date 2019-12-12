import click
import logging
from pprint import pformat
from tabulate import tabulate
from lftools.api.endpoints import nexus


log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def task(ctx):
    pass


@task.command(name='list')
@click.pass_context
def list_tasks(ctx):
    r = ctx.obj['nexus']
    data = r.list_tasks()
    log.info(tabulate(data, headers=["Name", "Message", "Current State", "Last Run Result"]))

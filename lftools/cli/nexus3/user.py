import click
import logging
from pprint import pformat
from tabulate import tabulate
from lftools.api.endpoints import nexus


log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def user(ctx):
    pass


@user.command(name='search')
@click.argument('username')
@click.pass_context
def search_user(ctx, username):
    r = ctx.obj['nexus']
    data = r.list_user(username)
    log.info(tabulate(data, headers=["User ID", "First Name", "Last Name", "Email Address", "Status", "Roles"]))

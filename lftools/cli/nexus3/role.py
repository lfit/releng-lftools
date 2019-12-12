import click
import logging
from pprint import pformat
from tabulate import tabulate
from lftools.api.endpoints import nexus


log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def role(ctx):
    pass


@role.command(name='list')
@click.pass_context
def list_roles(ctx):
    r = ctx.obj['nexus']
    data = r.list_roles()
    log.info(tabulate(data, headers=["Roles"]))


@role.command(name='create')
@click.argument('name')
@click.argument('description')
@click.argument('privileges')
@click.argument('roles')
@click.pass_context
def create_role(ctx, name, description, privileges, roles):
    r = ctx.obj['nexus']
    data = r.create_role(name, description, privileges, roles)
    log.info(pformat(data))



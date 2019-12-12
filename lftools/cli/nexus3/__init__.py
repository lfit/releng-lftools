from .asset import *
from .privilege import *
from .repository import *
from .role import *
from .script import *
from .task import *
from .user import *


@click.group()
@click.argument('fqdn')
@click.pass_context
def nexus3(ctx, fqdn):
    """Provide an interface to Nexus3."""
    nexus_obj = nexus.Nexus(fqdn=fqdn)
    ctx.obj = {
        'nexus': nexus_obj
    }
    pass


nexus3.add_command(asset)
nexus3.add_command(privilege)
nexus3.add_command(repository)
nexus3.add_command(role)
nexus3.add_command(script)
nexus3.add_command(task)
nexus3.add_command(user)

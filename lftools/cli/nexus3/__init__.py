from .script import *


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


nexus3.add_command(script)

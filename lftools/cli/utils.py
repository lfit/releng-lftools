import click
import logging

from lftools import helpers

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def utils(ctx):
    """Tools to make life easier."""
    pass


@click.command(name="passgen")
@click.argument("length", required=False)
@click.pass_context
def password_generator(ctx, length):
    """Generate a complex password.

    Length defaults to 12 characters if not specified.
    """
    if length:
        length = int(length)
    else:
        length = 12
    log.info(helpers.generate_password(length))


utils.add_command(password_generator)

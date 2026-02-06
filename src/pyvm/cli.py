import click
from . import doctor_command

@click.group()
def cli():
    pass

@cli.command()
def doctor():
    """Run health checks for pyvm environment."""
    doctor_command()
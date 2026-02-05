import click
from . import run_doctor

@click.command()
def doctor():
    """Run health checks on pyvm setup."""
    run_doctor()
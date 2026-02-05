import click
from .health_check import run_health_checks

@click.group()
def cli():
    pass

@cli.command()
def doctor():
    """Run health checks on the pyvm installation."""
    run_health_checks()
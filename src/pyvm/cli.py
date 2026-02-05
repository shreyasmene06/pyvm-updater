import click
from .commands import doctor

@click.group()
def cli():
    pass

cli.add_command(doctor.doctor)
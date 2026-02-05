import click
from .doctor import doctor

@click.group()
def cli():
    """Python Version Manager CLI"""
    pass

cli.add_command(doctor)

if __name__ == "__main__":
    cli()
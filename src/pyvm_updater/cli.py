import click
from . import __version__
from .core import install_version, remove_version

@click.group()
@click.version_option(__version__)
def main():
    """pyvm-updater CLI"""
    pass

@main.command()
@click.argument('version')
@click.option('--dry-run', is_flag=True, help="Preview the installation without making changes.")
def install(version, dry_run):
    """Install a specific Python version."""
    if dry_run:
        click.echo(f"[DRY-RUN] Would install Python version: {version}")
    else:
        install_version(version)
        click.echo(f"Successfully installed Python {version}")

@main.command()
@click.argument('version')
@click.option('--dry-run', is_flag=True, help="Preview the removal without making changes.")
def remove(version, dry_run):
    """Remove a specific Python version."""
    if dry_run:
        click.echo(f"[DRY-RUN] Would remove Python version: {version}")
    else:
        remove_version(version)
        click.echo(f"Successfully removed Python {version}")

if __name__ == '__main__':
    main()
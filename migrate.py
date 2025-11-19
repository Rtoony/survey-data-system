#!/usr/bin/env python3
"""
Database Migration CLI
Provides Flask commands for managing Alembic migrations

Usage:
    python migrate.py db init       # Initialize migrations (already done)
    python migrate.py db revision --message "description"  # Create empty migration
    python migrate.py db migrate --message "description"   # Generate migration from models
    python migrate.py db upgrade                           # Apply migrations
    python migrate.py db downgrade                         # Rollback migrations
    python migrate.py db current                           # Show current revision
    python migrate.py db history                           # Show migration history
"""
import os
import sys
import click
from alembic import command
from alembic.config import Config as AlembicConfig
from app import create_app


def get_alembic_config() -> AlembicConfig:
    """
    Create and configure an Alembic Config object.

    Returns:
        Configured AlembicConfig instance
    """
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    alembic_ini_path = os.path.join(project_root, 'alembic.ini')

    # Create Alembic config
    alembic_cfg = AlembicConfig(alembic_ini_path)

    # Set the script location
    alembic_cfg.set_main_option('script_location', os.path.join(project_root, 'migrations'))

    return alembic_cfg


@click.group()
def cli():
    """Database migration commands."""
    pass


@cli.group()
def db():
    """Database migration management commands."""
    pass


@db.command()
@click.option('-m', '--message', required=True, help='Migration message')
def revision(message: str):
    """
    Create a new empty migration revision.

    This creates a blank migration file that you can manually edit.
    """
    click.echo(f"Creating new revision: {message}")
    alembic_cfg = get_alembic_config()
    command.revision(alembic_cfg, message=message, autogenerate=False)
    click.echo("✓ Migration file created successfully!")


@db.command()
@click.option('-m', '--message', required=True, help='Migration message')
def migrate(message: str):
    """
    Generate a new migration revision using autogenerate.

    This compares your SQLAlchemy models with the database schema
    and generates a migration to sync them.
    """
    click.echo(f"Generating migration: {message}")
    click.echo("Comparing models to database schema...")

    alembic_cfg = get_alembic_config()

    try:
        command.revision(alembic_cfg, message=message, autogenerate=True)
        click.echo("✓ Migration generated successfully!")
        click.echo("\nIMPORTANT: Review the generated migration file before applying it.")
        click.echo("Autogenerate may not detect all changes (like custom types, constraints, etc.)")
    except Exception as e:
        click.echo(f"✗ Error generating migration: {e}", err=True)
        sys.exit(1)


@db.command()
@click.option('-r', '--revision', default='head', help='Revision to upgrade to (default: head)')
@click.option('--sql', is_flag=True, help='Generate SQL instead of executing')
def upgrade(revision: str, sql: bool):
    """
    Upgrade database to a later version.

    By default, upgrades to the latest version ('head').
    """
    if sql:
        click.echo(f"Generating SQL for upgrade to {revision}...")
        alembic_cfg = get_alembic_config()
        command.upgrade(alembic_cfg, revision, sql=True)
    else:
        click.echo(f"Upgrading database to {revision}...")
        alembic_cfg = get_alembic_config()

        try:
            command.upgrade(alembic_cfg, revision)
            click.echo("✓ Database upgraded successfully!")
        except Exception as e:
            click.echo(f"✗ Error upgrading database: {e}", err=True)
            sys.exit(1)


@db.command()
@click.option('-r', '--revision', default='-1', help='Revision to downgrade to (default: -1)')
@click.option('--sql', is_flag=True, help='Generate SQL instead of executing')
def downgrade(revision: str, sql: bool):
    """
    Downgrade database to an earlier version.

    By default, downgrades by one version.
    """
    if sql:
        click.echo(f"Generating SQL for downgrade to {revision}...")
        alembic_cfg = get_alembic_config()
        command.downgrade(alembic_cfg, revision, sql=True)
    else:
        click.echo(f"Downgrading database to {revision}...")
        alembic_cfg = get_alembic_config()

        try:
            command.downgrade(alembic_cfg, revision)
            click.echo("✓ Database downgraded successfully!")
        except Exception as e:
            click.echo(f"✗ Error downgrading database: {e}", err=True)
            sys.exit(1)


@db.command()
def current():
    """Show current database revision."""
    click.echo("Current database revision:")
    alembic_cfg = get_alembic_config()
    command.current(alembic_cfg, verbose=True)


@db.command()
@click.option('-v', '--verbose', is_flag=True, help='Show detailed history')
def history(verbose: bool):
    """Show migration history."""
    click.echo("Migration history:")
    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg, verbose=verbose)


@db.command()
def heads():
    """Show current available heads in the script directory."""
    click.echo("Current heads:")
    alembic_cfg = get_alembic_config()
    command.heads(alembic_cfg, verbose=True)


@db.command()
@click.option('-r', '--revision', required=True, help='Revision ID')
def show(revision: str):
    """Show details about a specific revision."""
    click.echo(f"Showing details for revision {revision}:")
    alembic_cfg = get_alembic_config()
    command.show(alembic_cfg, revision)


@db.command()
@click.option('-m', '--message', required=True, help='Migration message')
def stamp(message: str):
    """
    'Stamp' the revision table with a specific revision.

    This doesn't run any migrations - it just sets the current
    database version. Useful for initializing the migration
    history on an existing database.
    """
    click.echo(f"Stamping database with revision: {message}")
    alembic_cfg = get_alembic_config()

    try:
        command.stamp(alembic_cfg, message)
        click.echo("✓ Database stamped successfully!")
    except Exception as e:
        click.echo(f"✗ Error stamping database: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()

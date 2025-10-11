"""Command-line interface for Moderator"""

import click
from .orchestrator import Orchestrator


@click.group()
def cli():
    """Moderator - AI Code Generation Orchestration System"""
    pass


@cli.command()
@click.argument('request')
@click.option('--db', default='moderator.db', help='Database path')
def execute(request: str, db: str):
    """Execute a code generation request"""
    orchestrator = Orchestrator(db_path=db)

    try:
        result = orchestrator.execute(request)

        if result.status == "success":
            click.echo(click.style("\n✅ Execution completed successfully", fg="green"))
        else:
            click.echo(click.style(f"\n⚠️  Execution completed with status: {result.status}", fg="yellow"))

    except Exception as e:
        click.echo(click.style(f"\n❌ Execution failed: {str(e)}", fg="red"))
        raise


@cli.command()
@click.argument('execution_id')
@click.option('--db', default='moderator.db', help='Database path')
def status(execution_id: str, db: str):
    """Check status of an execution"""
    from .state_manager import StateManager

    state = StateManager(db_path=db)
    execution = state.get_execution(execution_id)

    if execution:
        click.echo(f"\nExecution: {execution['id']}")
        click.echo(f"Request: {execution['request']}")
        click.echo(f"Status: {execution['status']}")
        click.echo(f"Created: {execution['created_at']}")
        if execution['completed_at']:
            click.echo(f"Completed: {execution['completed_at']}")
    else:
        click.echo(click.style(f"Execution {execution_id} not found", fg="red"))


@cli.command()
@click.option('--db', default='moderator.db', help='Database path')
def list_executions(db: str):
    """List recent executions"""
    from .state_manager import StateManager
    import sqlite3

    state = StateManager(db_path=db)
    cursor = state.conn.cursor()
    cursor.execute("""
        SELECT id, request, status, created_at
        FROM executions
        ORDER BY created_at DESC
        LIMIT 10
    """)

    executions = cursor.fetchall()

    if executions:
        click.echo("\nRecent Executions:")
        click.echo("-" * 80)
        for exec_id, request, status, created_at in executions:
            status_color = "green" if status == "completed" else "yellow" if status == "running" else "red"
            status_display = click.style(status.ljust(12), fg=status_color)
            click.echo(f"{exec_id} | {status_display} | {created_at} | {request[:50]}")
    else:
        click.echo("No executions found")


if __name__ == '__main__':
    cli()

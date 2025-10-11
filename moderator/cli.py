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


@cli.command()
@click.argument('execution_id')
@click.option('--rounds', default=5, help='Maximum improvement rounds')
@click.option('--db', default='moderator.db', help='Database path')
def improve(execution_id: str, rounds: int, db: str):
    """Run iterative improvement on an execution"""
    from .state_manager import StateManager
    import sqlite3

    state = StateManager(db_path=db)
    orch = Orchestrator(db_path=db)

    # Get execution result from database
    cursor = state.conn.cursor()
    cursor.execute("""
        SELECT r.id, r.task_id, r.backend, r.files, r.metadata, r.execution_time
        FROM results r
        JOIN tasks t ON r.task_id = t.id
        WHERE t.execution_id = ?
        LIMIT 1
    """, (execution_id,))

    row = cursor.fetchone()
    if not row:
        click.echo(click.style(f"No results found for execution {execution_id}", fg="red"))
        return

    import json
    from .models import ExecutionResult, CodeOutput, BackendType

    result_id, task_id, backend, files_json, metadata_json, exec_time = row

    # Reconstruct result
    result = ExecutionResult(
        task_id=task_id,
        execution_id=execution_id,
        backend=BackendType(backend),
        output=CodeOutput(
            files=json.loads(files_json),
            metadata=json.loads(metadata_json) if metadata_json else {},
            backend=backend,
            execution_time=exec_time or 0.0
        ),
        issues=[],
        improvements=[],
        status="success"
    )

    click.echo(f"\n🔄 Starting iterative improvement...")
    click.echo(f"Execution: {execution_id}")
    click.echo(f"Max rounds: {rounds}\n")

    # Run improvement
    try:
        improvement_rounds = orch.improve_iteratively(result, max_rounds=rounds)
        click.echo(click.style(f"\n✅ Completed {len(improvement_rounds)-1} improvement rounds", fg="green"))
    except Exception as e:
        click.echo(click.style(f"\n❌ Improvement failed: {str(e)}", fg="red"))
        raise


if __name__ == '__main__':
    cli()

"""Unified CLI for Maestro — serve, run, start, validate, export."""

import logging
import os
import sys

import click
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def _load_env() -> None:
    """Load .env file from current working directory."""
    load_dotenv(override=False)


def _setup_logging(verbose: bool = False) -> None:
    """Configure logging with Rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    try:
        from rich.logging import RichHandler

        logging.basicConfig(level=level, format="%(message)s", handlers=[RichHandler(rich_tracebacks=True)])
    except ImportError:
        logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Maestro — Unified Scrum Planner + Agent Orchestrator."""
    _load_env()
    _setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option("--port", default=8000, help="Port to serve on")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
def serve(port: int, host: str) -> None:
    """Start the web server (planner UI + dashboard)."""
    import uvicorn

    from maestro.api.app import create_app

    app = create_app()
    logger.info("Starting Maestro web server on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)


@cli.command()
@click.option("--config", "config_path", default=None, help="Path to workflow.yaml")
def run(config_path: str | None) -> None:
    """Start the orchestrator daemon only (no web server)."""
    import asyncio

    from maestro.runner.orchestrator import Orchestrator
    from maestro.runner.workflow_config import parse_workflow_file

    if config_path is None:
        config_path = _find_workflow_file()
        if config_path is None:
            click.echo("No workflow.yaml found. Use --config to specify one.", err=True)
            sys.exit(1)

    config = parse_workflow_file(config_path)
    orch = Orchestrator(config, workflow_dir=os.path.dirname(os.path.abspath(config_path)))
    logger.info("Starting orchestrator daemon with config: %s", config_path)
    asyncio.run(orch.run())


@cli.command()
@click.option("--port", default=8000, help="Port to serve on")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--config", "config_path", default=None, help="Path to workflow.yaml")
def start(port: int, host: str, config_path: str | None) -> None:
    """Start both the web server and orchestrator daemon."""

    import uvicorn

    from maestro.api.app import create_app

    app = create_app()

    if config_path:
        from maestro.runner.orchestrator import Orchestrator
        from maestro.runner.workflow_config import parse_workflow_file

        config = parse_workflow_file(config_path)
        orch = Orchestrator(config, workflow_dir=os.path.dirname(os.path.abspath(config_path)))
        # Store orchestrator on the app for the API to access
        app.state.orchestrator = orch

    logger.info("Starting Maestro (web + orchestrator) on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)


@cli.command()
@click.argument("config_path")
def validate(config_path: str) -> None:
    """Validate a workflow.yaml configuration file."""
    from maestro.runner.workflow_config import parse_workflow_file, validate_config

    try:
        config = parse_workflow_file(config_path)
        errors = validate_config(config)
        if errors:
            click.echo("Validation errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        else:
            click.echo(f"Config valid: {len(config.states)} states, entry={config.entry_state}")
    except Exception as e:
        click.echo(f"Failed to parse config: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("session_id")
@click.option("--format", "fmt", type=click.Choice(["linear", "markdown", "html"]), default="html")
@click.option("--output", "-o", default=None, help="Output path")
def export(session_id: str, fmt: str, output: str | None) -> None:
    """Export a saved planning session."""
    click.echo(f"Exporting session {session_id} as {fmt}...")
    if fmt == "html":

        # TODO: Load session state from storage
        click.echo("HTML export not yet connected to session storage.", err=True)
    elif fmt == "markdown":
        click.echo("Markdown export not yet implemented.", err=True)
    elif fmt == "linear":
        click.echo("Linear export not yet implemented.", err=True)


def _find_workflow_file() -> str | None:
    """Auto-detect workflow.yaml in current directory."""
    for name in ("workflow.yaml", "workflow.yml"):
        if os.path.isfile(name):
            return name
    return None


def main() -> None:
    """Entry point for the maestro CLI."""
    cli()

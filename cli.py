"""CLI interface for Loctor Builder - AI-Powered Autonomous Locator Validator."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from core.auditor import Auditor
from core.config_manager import ConfigManager

console = Console()


def _banner() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Loctor Builder[/bold cyan]\n"
            "[dim]AI-Powered Autonomous Locator Validator[/dim]",
            border_style="cyan",
        )
    )


@click.group()
@click.option(
    "--config", "-c", default="config.json", help="Path to config.json file"
)
@click.pass_context
def cli(ctx: click.Context, config: str) -> None:
    """Loctor Builder - AI-Powered Autonomous Locator Validator"""
    ctx.ensure_object(dict)
    try:
        ctx.obj["config"] = ConfigManager(config)
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {config}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("script_path")
@click.option("--repo", "-r", default=None, help="Path to the Git repository")
@click.option("--provider", "-p", default=None, help="AI provider to use (gemini/openai/claude)")
@click.option("--headless/--no-headless", default=None, help="Run browser headless")
@click.pass_context
def audit(
    ctx: click.Context,
    script_path: str,
    repo: str | None,
    provider: str | None,
    headless: bool | None,
) -> None:
    """Run the locator audit on an automation script."""
    _banner()
    config: ConfigManager = ctx.obj["config"]

    if provider:
        try:
            config.active_provider = provider
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            sys.exit(1)

    if headless is not None:
        config.set_setting("headless", headless)

    console.print(f"[cyan]Script:[/cyan]  {script_path}")
    console.print(f"[cyan]Provider:[/cyan] {config.active_provider}")
    console.print(f"[cyan]Headless:[/cyan] {config.get_setting('headless', True)}")
    console.print()

    auditor = Auditor(config)
    elements_done = 0

    def on_element(result):
        nonlocal elements_done
        elements_done += 1
        status_color = {
            "passed": "green",
            "healed": "yellow",
            "failed": "red",
            "skipped": "dim",
        }
        color = status_color.get(result.status.value, "white")
        console.print(
            f"  [{color}]{result.status.value.upper():>7}[/{color}] "
            f"{result.element_name} ({result.original_locator.selector_string})"
        )

    def on_page(page_name, url):
        console.print(f"\n[bold blue]Page: {page_name}[/bold blue] ({url})")

    auditor.set_callbacks(on_element_audited=on_element, on_page_started=on_page)

    try:
        report = asyncio.run(auditor.run_audit(script_path, repo))
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Audit failed: {e}[/red]")
        sys.exit(1)

    console.print()
    _print_summary(report)


@cli.command()
@click.argument("provider", type=click.Choice(["gemini", "openai", "claude"]))
@click.pass_context
def switch(ctx: click.Context, provider: str) -> None:
    """Switch the active AI provider at runtime."""
    config: ConfigManager = ctx.obj["config"]
    old = config.active_provider
    try:
        config.active_provider = provider
        console.print(f"[green]Switched provider: {old} -> {provider}[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show current configuration status."""
    _banner()
    config: ConfigManager = ctx.obj["config"]
    safe_config = config.to_dict()

    table = Table(title="Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    table.add_row("Active Provider", safe_config.get("active_provider", ""))

    for name, prov in safe_config.get("providers", {}).items():
        marker = " [green](active)[/green]" if name == safe_config["active_provider"] else ""
        table.add_row(f"  {name}{marker}", f"model={prov.get('model', 'N/A')}")

    for key, val in safe_config.get("settings", {}).items():
        table.add_row(f"  {key}", str(val))

    console.print(table)


@cli.command()
@click.pass_context
def providers(ctx: click.Context) -> None:
    """List all configured AI providers."""
    config: ConfigManager = ctx.obj["config"]
    table = Table(title="AI Providers", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Model")
    table.add_column("Status")

    for name in config.get_all_providers():
        prov_cfg = config.get_provider_config(name)
        is_active = name == config.active_provider
        has_key = prov_cfg.get("api_key", "YOUR_KEY_HERE") != "YOUR_KEY_HERE"
        status_str = "[green]Active[/green]" if is_active else ""
        if not has_key:
            status_str += " [red](no API key)[/red]"
        table.add_row(name, prov_cfg.get("model", ""), status_str)

    console.print(table)


@cli.command()
@click.pass_context
def dashboard(ctx: click.Context) -> None:
    """Launch the web-based monitoring dashboard."""
    config: ConfigManager = ctx.obj["config"]
    port = config.get_setting("dashboard_port", 5050)
    console.print(f"[cyan]Starting dashboard on http://localhost:{port}[/cyan]")

    from ui.dashboard import create_app

    app, socketio = create_app(config)
    socketio.run(app, host="0.0.0.0", port=port, debug=False)


def _print_summary(report) -> None:
    """Print a summary table of the audit report."""
    table = Table(title="Audit Summary", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Total Elements", str(report.total_elements))
    table.add_row("Passed", f"[green]{report.passed}[/green]")
    table.add_row("Healed", f"[yellow]{report.healed}[/yellow]")
    table.add_row("Failed", f"[red]{report.failed}[/red]")
    table.add_row("Success Rate", f"{report.success_rate:.1f}%")
    table.add_row("Provider", report.ai_provider_used)

    if report.start_time and report.end_time:
        duration = report.end_time - report.start_time
        table.add_row("Duration", str(duration))

    console.print(table)


if __name__ == "__main__":
    cli()

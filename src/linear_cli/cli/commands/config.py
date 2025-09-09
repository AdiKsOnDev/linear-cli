"""
Configuration commands for Linearator CLI.

Handles configuration viewing, editing, and management.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()


@click.group()
def config_group() -> None:
    """Configuration management commands."""
    pass


@config_group.command()
@click.pass_context
def show(ctx: click.Context) -> None:
    """Show current configuration."""
    cli_ctx = ctx.obj["cli_context"]
    config = cli_ctx.config

    console.print("[bold]Current Configuration[/bold]")
    console.print()

    # Create table for configuration display
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Setting", style="dim")
    table.add_column("Value")
    table.add_column("Source", style="dim")

    # Configuration values (hide sensitive data)
    config_items = [
        ("API URL", config.api_url, "config"),
        ("Default Team ID", config.default_team_id or "Not set", "config"),
        ("Default Team Key", config.default_team_key or "Not set", "config"),
        ("Output Format", config.output_format, "config"),
        ("Timeout", f"{config.timeout}s", "config"),
        ("Max Retries", str(config.max_retries), "config"),
        ("Cache TTL", f"{config.cache_ttl}s", "config"),
        ("Verbose Logging", "Yes" if config.verbose else "No", "config"),
        ("Debug Logging", "Yes" if config.debug else "No", "config"),
        ("No Color", "Yes" if config.no_color else "No", "config"),
        ("Client ID", "Set" if config.client_id else "Not set", "config"),
        ("Client Secret", "Set" if config.client_secret else "Not set", "config"),
        ("Access Token", "Set" if config.access_token else "Not set", "config"),
    ]

    for setting, value, source in config_items:
        table.add_row(setting, str(value), source)

    console.print(table)

    # Show config file location
    config_info = cli_ctx.config_manager.get_config_info()
    console.print()
    console.print(f"[dim]Config file:[/dim] {config_info['config_file']}")
    console.print(f"[dim]Config directory:[/dim] {config_info['config_dir']}")


@config_group.command()
@click.argument("key")
@click.argument("value")
@click.pass_context
def set(ctx: click.Context, key: str, value: str) -> None:
    """Set a configuration value."""
    cli_ctx = ctx.obj["cli_context"]

    # Map of CLI keys to config attributes
    key_mapping = {
        "api-url": "api_url",
        "team-id": "default_team_id",
        "team-key": "default_team_key",
        "output-format": "output_format",
        "timeout": "timeout",
        "max-retries": "max_retries",
        "cache-ttl": "cache_ttl",
        "client-id": "client_id",
        "client-secret": "client_secret",
    }

    if key not in key_mapping:
        console.print(f"[red]Unknown configuration key: {key}[/red]")
        console.print("Available keys:")
        for k in key_mapping.keys():
            console.print(f"  - {k}")
        raise click.Abort()

    config_key = key_mapping[key]

    # Type conversion for specific keys
    converted_value: str | int = value
    if key in ("timeout", "max-retries", "cache-ttl"):
        try:
            converted_value = int(value)
        except ValueError:
            console.print(f"[red]Invalid value for {key}: must be an integer[/red]")
            raise click.Abort() from None

    elif key == "output-format":
        if value not in ("table", "json", "yaml"):
            console.print(f"[red]Invalid output format: {value}[/red]")
            console.print("Valid formats: table, json, yaml")
            raise click.Abort()

    try:
        cli_ctx.config_manager.update_config(**{config_key: converted_value})
        console.print(f"[green]✓ Set {key} = {converted_value}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration: {e}[/red]")
        raise click.Abort() from None


@config_group.command()
@click.argument("key")
@click.pass_context
def unset(ctx: click.Context, key: str) -> None:
    """Unset a configuration value."""
    cli_ctx = ctx.obj["cli_context"]

    key_mapping = {
        "team-id": "default_team_id",
        "team-key": "default_team_key",
        "client-id": "client_id",
        "client-secret": "client_secret",
    }

    if key not in key_mapping:
        console.print(f"[red]Cannot unset configuration key: {key}[/red]")
        console.print("Keys that can be unset:")
        for k in key_mapping.keys():
            console.print(f"  - {k}")
        raise click.Abort()

    config_key = key_mapping[key]

    try:
        cli_ctx.config_manager.update_config(**{config_key: None})
        console.print(f"[green]✓ Unset {key}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration: {e}[/red]")
        raise click.Abort() from None


@config_group.command()
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def reset(ctx: click.Context, confirm: bool) -> None:
    """Reset configuration to defaults."""
    cli_ctx = ctx.obj["cli_context"]

    if not confirm:
        confirm_reset = Prompt.ask(
            "This will reset all configuration to defaults. Continue?",
            choices=["y", "n"],
            default="n",
        )

        if confirm_reset.lower() != "y":
            console.print("Configuration reset cancelled.")
            return

    try:
        cli_ctx.config_manager.reset_config()
        console.print("[green]✓ Configuration reset to defaults[/green]")
        console.print("Note: You may need to re-authenticate.")
    except Exception as e:
        console.print(f"[red]Failed to reset configuration: {e}[/red]")
        raise click.Abort() from None


@config_group.command()
@click.pass_context
def edit(ctx: click.Context) -> None:
    """Edit configuration file in default editor."""
    import os
    import subprocess

    cli_ctx = ctx.obj["cli_context"]
    config_file = cli_ctx.config_manager.config_file

    # Get editor from environment - validated against safe editors
    editor = os.environ.get("EDITOR", "nano")
    
    # Validate editor is a safe, known editor
    safe_editors = {"nano", "vim", "vi", "emacs", "code", "subl", "atom", "gedit"}
    editor_name = Path(editor).name
    
    if editor_name not in safe_editors:
        console.print(f"[red]✗ Editor '{editor}' not in safe editors list[/red]")
        console.print("Set EDITOR to one of: " + ", ".join(sorted(safe_editors)))
        return

    try:
        # nosec B603 - editor validated against safe list above
        subprocess.run([editor, str(config_file)], check=True)
        console.print(f"[green]✓ Configuration file edited with {editor}[/green]")
        console.print("Note: Changes will take effect on next command.")
    except subprocess.CalledProcessError:
        console.print(f"[red]Failed to open editor: {editor}[/red]")
        console.print(
            f"Set EDITOR environment variable or edit manually: {config_file}"
        )
        raise click.Abort() from None
    except FileNotFoundError:
        console.print(f"[red]Editor not found: {editor}[/red]")
        console.print(
            f"Set EDITOR environment variable or edit manually: {config_file}"
        )
        raise click.Abort() from None

"""
Authentication commands for Linearator CLI.

Handles login, logout, and authentication status commands.
"""

import asyncio
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

import click
from rich.console import Console
from rich.prompt import Prompt

from ...api.auth import AuthenticationError, OAuthFlowError

console = Console()


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    def __init__(self, expected_state: str, *args: Any, **kwargs: Any):
        self.expected_state = expected_state
        self.auth_code: str | None = None
        self.auth_state: str | None = None
        self.auth_error: str | None = None
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET request for OAuth callback."""
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        # Check for authorization code
        if "code" in params and "state" in params:
            self.auth_code = params["code"][0]
            self.auth_state = params["state"][0]

            # Send success response
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

            success_html = """
            <html>
            <head><title>Authentication Successful</title></head>
            <body>
                <h1>Authentication Successful!</h1>
                <p>You can now close this window and return to the terminal.</p>
                <script>setTimeout(function(){window.close();}, 3000);</script>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())

        elif "error" in params:
            # Handle OAuth error
            self.auth_error = params.get("error_description", [params["error"][0]])[0]

            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

            error_html = f"""
            <html>
            <head><title>Authentication Failed</title></head>
            <body>
                <h1>Authentication Failed</h1>
                <p>Error: {self.auth_error}</p>
                <p>Please close this window and try again.</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())

        else:
            # Invalid request
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Invalid OAuth callback request")

    def log_message(self, format, *args):
        """Suppress log messages from HTTP server."""
        pass


def start_oauth_callback_server(
    expected_state: str, port: int = 8080
) -> tuple[HTTPServer, Any]:
    """
    Start HTTP server to handle OAuth callback.

    Returns:
        Tuple of (server, handler_instance)
    """

    def handler_factory(*args, **kwargs):
        handler = OAuthCallbackHandler(expected_state, *args, **kwargs)
        handler_factory.handler = handler
        return handler

    handler_factory.handler = None

    server = HTTPServer(("localhost", port), handler_factory)

    # Start server in a separate thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    return server, handler_factory


@click.group()
def auth_group() -> None:
    """Authentication commands."""
    pass


@auth_group.command()
@click.option("--api-key", help="Linear API key for direct authentication")
@click.option("--client-id", help="OAuth client ID")
@click.option("--client-secret", help="OAuth client secret")
@click.option("--no-browser", is_flag=True, help="Don't automatically open browser")
@click.pass_context
def login(
    ctx: click.Context,
    api_key: str | None,
    client_id: str | None,
    client_secret: str | None,
    no_browser: bool,
) -> None:
    """
    Authenticate with Linear.

    You can authenticate using either:
    1. OAuth flow (recommended for interactive use)
    2. API key (for automation and scripts)

    For OAuth, you'll need client credentials from Linear's developer settings.
    For API key authentication, generate a personal access token in Linear.

    Examples:
        linearator auth login                          # OAuth flow
        linearator auth login --api-key YOUR_KEY      # API key
    """
    cli_ctx = ctx.obj["cli_context"]
    authenticator = cli_ctx.authenticator

    if api_key:
        # API key authentication
        console.print("Authenticating with API key...")

        try:
            authenticator.authenticate_with_api_key(api_key)
            console.print("[green]✓ Successfully authenticated with API key![/green]")

            # Test connection
            console.print("Testing connection...")
            client = cli_ctx.get_client()

            async def test_auth():
                viewer = await client.get_viewer()
                return viewer

            viewer = asyncio.run(test_auth())
            console.print(
                f"[green]✓ Connected as {viewer.get('name', 'Unknown User')}[/green]"
            )

        except AuthenticationError as e:
            console.print(f"[red]✗ Authentication failed: {e}[/red]")
            raise click.Abort() from None
        except Exception as e:
            console.print(f"[red]✗ Unexpected error: {e}[/red]")
            raise click.Abort() from None

    else:
        # OAuth flow
        console.print("Starting OAuth authentication flow...")

        # Use provided credentials or ask for them
        if not client_id:
            client_id = cli_ctx.config.client_id or Prompt.ask(
                "Enter your Linear OAuth client ID"
            )

        if not client_secret:
            client_secret = cli_ctx.config.client_secret or Prompt.ask(
                "Enter your Linear OAuth client secret", password=True
            )

        if not client_id or not client_secret:
            console.print("[red]OAuth client ID and secret are required.[/red]")
            console.print("Get them from: https://linear.app/settings/api/oauth-apps")
            raise click.Abort()

        # Update authenticator with OAuth credentials
        authenticator.client_id = client_id
        authenticator.client_secret = client_secret

        try:
            # Start OAuth flow
            auth_url, state = authenticator.start_oauth_flow()

            console.print("Opening Linear authorization page in your browser...")
            console.print(
                f"If the browser doesn't open automatically, visit: {auth_url}"
            )
            console.print()

            # Start callback server
            server, handler_factory = start_oauth_callback_server(state)

            try:
                # Open browser unless disabled
                if not no_browser:
                    webbrowser.open(auth_url)

                console.print("Waiting for authorization... (press Ctrl+C to cancel)")

                # Wait for callback
                timeout = 300  # 5 minutes
                start_time = time.time()

                while time.time() - start_time < timeout:
                    handler = handler_factory.handler
                    if handler and (handler.auth_code or handler.auth_error):
                        break
                    time.sleep(0.5)
                else:
                    console.print("[red]✗ Authentication timed out.[/red]")
                    raise click.Abort()

                handler = handler_factory.handler

                if handler.auth_error:
                    console.print(f"[red]✗ OAuth error: {handler.auth_error}[/red]")
                    raise click.Abort()

                if not handler.auth_code:
                    console.print("[red]✗ No authorization code received.[/red]")
                    raise click.Abort()

                # Complete OAuth flow
                console.print("Completing authentication...")
                authenticator.complete_oauth_flow(
                    handler.auth_code, handler.auth_state, state
                )

                console.print("[green]✓ Successfully authenticated with OAuth![/green]")

                # Test connection
                console.print("Testing connection...")
                client = cli_ctx.get_client()

                async def test_auth():
                    viewer = await client.get_viewer()
                    return viewer

                viewer = asyncio.run(test_auth())
                console.print(
                    f"[green]✓ Connected as {viewer.get('name', 'Unknown User')}[/green]"
                )

                # Save OAuth credentials to config if they're not already there
                if not cli_ctx.config.client_id or not cli_ctx.config.client_secret:
                    save_creds = Prompt.ask(
                        "Save OAuth credentials to config for future use?",
                        choices=["y", "n"],
                        default="y",
                    )

                    if save_creds.lower() == "y":
                        cli_ctx.config_manager.update_config(
                            client_id=client_id, client_secret=client_secret
                        )
                        console.print(
                            "[green]✓ OAuth credentials saved to config.[/green]"
                        )

            finally:
                server.shutdown()
                server.server_close()

        except OAuthFlowError as e:
            console.print(f"[red]✗ OAuth flow failed: {e}[/red]")
            raise click.Abort() from None
        except AuthenticationError as e:
            console.print(f"[red]✗ Authentication failed: {e}[/red]")
            raise click.Abort() from None
        except KeyboardInterrupt:
            console.print("\n[yellow]Authentication cancelled by user.[/yellow]")
            raise click.Abort() from None
        except Exception as e:
            console.print(f"[red]✗ Unexpected error: {e}[/red]")
            if cli_ctx.config.debug:
                console.print_exception()
            raise click.Abort() from None


@auth_group.command()
@click.pass_context
def logout(ctx: click.Context) -> None:
    """
    Log out and clear stored credentials.

    This will remove all stored authentication tokens and credentials
    from your system. You will need to authenticate again to use Linearator.
    """
    cli_ctx = ctx.obj["cli_context"]

    try:
        cli_ctx.authenticator.logout()
        console.print("[green]✓ Successfully logged out.[/green]")
        console.print("All stored credentials have been cleared.")
    except Exception as e:
        console.print(f"[yellow]Warning: Error during logout: {e}[/yellow]")
        console.print("[green]Logout completed (with warnings).[/green]")


@auth_group.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """
    Show authentication status and token information.

    Displays current authentication state, token type, expiration,
    and tests the connection to Linear's API.
    """
    cli_ctx = ctx.obj["cli_context"]
    authenticator = cli_ctx.authenticator

    console.print("[bold]Authentication Status[/bold]")
    console.print()

    is_authenticated = authenticator.is_authenticated
    console.print(
        f"[dim]Status:[/dim] {'✓ Authenticated' if is_authenticated else '✗ Not authenticated'}"
    )

    if is_authenticated:
        token_info = authenticator.get_token_info()

        console.print(
            f"[dim]Token type:[/dim] {token_info.get('token_type', 'unknown')}"
        )

        if token_info.get("expires_at"):
            expires = token_info["expires_at"]
            is_expired = token_info.get("is_expired", False)
            console.print(
                f"[dim]Expires:[/dim] {expires} {'(EXPIRED)' if is_expired else ''}"
            )
        else:
            console.print("[dim]Expires:[/dim] Never (API key)")

        console.print(
            f"[dim]Has refresh token:[/dim] {'Yes' if token_info.get('has_refresh_token') else 'No'}"
        )

        # Test API connection
        console.print()
        console.print("Testing API connection...")

        try:
            client = cli_ctx.get_client()

            async def test_connection():
                return await client.test_connection()

            result = asyncio.run(test_connection())

            if result["success"]:
                console.print(
                    f"[green]✓ Connected to Linear as {result['user']}[/green]"
                )
                console.print(f"[dim]Organization:[/dim] {result['organization']}")
                console.print(
                    f"[dim]Response time:[/dim] {result['response_time']:.2f}s"
                )
            else:
                console.print(f"[red]✗ Connection failed: {result['error']}[/red]")

        except Exception as e:
            console.print(f"[red]✗ Connection test failed: {e}[/red]")
            if cli_ctx.config.debug:
                console.print_exception()

    else:
        console.print()
        console.print(
            "[yellow]Not authenticated. Run 'linearator auth login' to authenticate.[/yellow]"
        )


@auth_group.command()
@click.pass_context
def refresh(ctx: click.Context) -> None:
    """
    Refresh authentication token.

    Attempts to refresh the current access token using the stored refresh token.
    This is only applicable for OAuth authentication, not API keys.
    """
    cli_ctx = ctx.obj["cli_context"]
    authenticator = cli_ctx.authenticator

    if not authenticator.is_authenticated:
        console.print("[red]✗ Not currently authenticated.[/red]")
        console.print("Run 'linearator auth login' to authenticate.")
        raise click.Abort()

    token_info = authenticator.get_token_info()

    if token_info.get("token_type") == "api_key":
        console.print(
            "[yellow]API keys don't need refreshing - they don't expire.[/yellow]"
        )
        return

    if not token_info.get("has_refresh_token"):
        console.print("[red]✗ No refresh token available.[/red]")
        console.print("You may need to re-authenticate with 'linearator auth login'.")
        raise click.Abort()

    try:
        console.print("Refreshing authentication token...")
        authenticator.refresh_token()
        console.print("[green]✓ Token refreshed successfully![/green]")

        # Test the new token
        console.print("Testing refreshed token...")
        client = cli_ctx.get_client()

        async def test_connection():
            return await client.test_connection()

        result = asyncio.run(test_connection())

        if result["success"]:
            console.print(
                f"[green]✓ Token is working - connected as {result['user']}[/green]"
            )
        else:
            console.print(
                f"[red]✗ Token refresh succeeded but connection failed: {result['error']}[/red]"
            )

    except AuthenticationError as e:
        console.print(f"[red]✗ Token refresh failed: {e}[/red]")
        console.print("You may need to re-authenticate with 'linearator auth login'.")
        raise click.Abort() from None
    except Exception as e:
        console.print(f"[red]✗ Unexpected error during token refresh: {e}[/red]")
        if cli_ctx.config.debug:
            console.print_exception()
        raise click.Abort() from None

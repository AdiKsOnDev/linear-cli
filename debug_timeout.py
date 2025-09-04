#!/usr/bin/env python3

import asyncio
from pathlib import Path
from unittest.mock import patch

from src.linearator.api.auth import LinearAuthenticator
from src.linearator.api.client import LinearClient
from src.linearator.config.manager import LinearConfig


async def test_client_creation():
    """Test creating LinearClient with real config."""
    print("Creating LinearConfig...")
    config = LinearConfig(
        debug=False,
        verbose=False,
        client_id="test_id",
        client_secret="test_secret",
        api_url="https://api.linear.app/graphql",
        timeout=30,
        max_retries=3,
        cache_ttl=300,
        cache_dir=Path("/tmp/cache"),
    )
    print(f"Config timeout: {config.timeout} ({type(config.timeout)})")

    print("Creating LinearAuthenticator...")
    authenticator = LinearAuthenticator(
        client_id=config.client_id,
        client_secret=config.client_secret
    )

    # Set up mock authentication
    authenticator._access_token = "test_token"

    print("Creating LinearClient...")
    try:
        client = LinearClient(
            config=config,
            authenticator=authenticator,
            enable_cache=False,
        )
        print("LinearClient created successfully")

        print("Testing get_viewer...")

        # Mock the GraphQL response
        mock_response = {"viewer": {"id": "test_user", "name": "Test User"}}

        with patch.object(client, 'execute_query', return_value=mock_response):
            result = await client.get_viewer()
            print(f"get_viewer result: {result}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_client_creation())

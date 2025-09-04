"""Performance benchmarks for Linearator CLI operations."""

import pytest

from linear_cli.api.client.client import LinearClient
from linear_cli.config.manager import LinearConfig


class TestPerformanceBenchmarks:
    """Performance benchmark tests for key operations."""

    @pytest.mark.benchmark
    def test_client_initialization_performance(self, benchmark):
        """Benchmark LinearClient initialization."""

        def create_client():
            config = LinearConfig()
            return LinearClient(config=config)

        # Benchmark the operation
        benchmark(create_client)

    @pytest.mark.benchmark
    def test_config_loading_performance(self, benchmark):
        """Benchmark configuration loading performance."""

        def load_config():
            return LinearConfig()

        # Benchmark the operation
        benchmark(load_config)

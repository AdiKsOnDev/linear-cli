"""Tests for constants module."""


from linearator.constants import (
    COLOR_PATTERNS,
    DEFAULT_API_TIMEOUT,
    DEFAULT_CACHE_TTL,
    DEFAULT_COLOR_STYLE,
    DEFAULT_ISSUE_LIMIT,
    DEFAULT_LABEL_LIMIT,
    DEFAULT_PRIORITY,
    DEFAULT_STATE_COLOR,
    HEX_COLOR_LENGTH,
    HEX_COLOR_PREFIX,
    LINEAR_API_RATE_LIMIT_WINDOW,
    MAX_ISSUE_LIMIT,
    OAUTH_CALLBACK_PORT,
    OAUTH_REDIRECT_URI,
    PRIORITY_LEVELS,
    TEAM_ID_MIN_LENGTH,
    TEAM_ID_PREFIX,
)


class TestConstants:
    """Test constants are properly defined."""

    def test_api_timeout_constants(self):
        """Test API timeout constants are defined."""
        assert isinstance(DEFAULT_API_TIMEOUT, int)
        assert DEFAULT_API_TIMEOUT > 0

        assert isinstance(DEFAULT_CACHE_TTL, int)
        assert DEFAULT_CACHE_TTL > 0

    def test_oauth_redirect_uri(self):
        """Test OAuth redirect URI is defined."""
        assert isinstance(OAUTH_REDIRECT_URI, str)
        assert OAUTH_REDIRECT_URI.startswith("http://")
        assert "localhost" in OAUTH_REDIRECT_URI

    def test_issue_limit_constants(self):
        """Test issue limit constants."""
        assert isinstance(DEFAULT_ISSUE_LIMIT, int)
        assert DEFAULT_ISSUE_LIMIT > 0

        assert isinstance(MAX_ISSUE_LIMIT, int)
        assert MAX_ISSUE_LIMIT > DEFAULT_ISSUE_LIMIT

        assert isinstance(DEFAULT_LABEL_LIMIT, int)
        assert DEFAULT_LABEL_LIMIT > 0

    def test_priority_levels(self):
        """Test priority levels are properly defined."""
        assert isinstance(PRIORITY_LEVELS, dict)
        assert len(PRIORITY_LEVELS) > 0

        # Check each priority level has text and style
        for priority, (text, style) in PRIORITY_LEVELS.items():
            assert isinstance(priority, int)
            assert isinstance(text, str)
            assert isinstance(style, str)
            assert len(text) > 0

    def test_default_priority(self):
        """Test default priority is valid."""
        assert isinstance(DEFAULT_PRIORITY, int)
        assert DEFAULT_PRIORITY in PRIORITY_LEVELS

    def test_color_patterns(self):
        """Test color patterns are properly defined."""
        assert isinstance(COLOR_PATTERNS, dict)
        assert len(COLOR_PATTERNS) > 0

        # Check each pattern has a color mapping
        for pattern, color in COLOR_PATTERNS.items():
            assert isinstance(pattern, str)
            assert isinstance(color, str)
            assert len(pattern) > 0
            assert len(color) > 0

    def test_team_constants(self):
        """Test team-related constants."""
        assert isinstance(TEAM_ID_PREFIX, str)
        assert len(TEAM_ID_PREFIX) > 0

        assert isinstance(TEAM_ID_MIN_LENGTH, int)
        assert TEAM_ID_MIN_LENGTH > 0

    def test_default_color_style(self):
        """Test default color style is defined."""
        assert isinstance(DEFAULT_COLOR_STYLE, str)
        assert len(DEFAULT_COLOR_STYLE) > 0

    def test_default_state_color(self):
        """Test default state color is defined."""
        assert isinstance(DEFAULT_STATE_COLOR, str)
        assert len(DEFAULT_STATE_COLOR) > 0

    def test_priority_levels_coverage(self):
        """Test that priority levels cover expected range."""
        # Should have priority levels 1-4 at minimum
        expected_priorities = [1, 2, 3, 4]
        for priority in expected_priorities:
            assert priority in PRIORITY_LEVELS, f"Priority {priority} missing"

    def test_hex_color_constants(self):
        """Test hex color validation constants."""
        assert isinstance(HEX_COLOR_PREFIX, str)
        assert HEX_COLOR_PREFIX == "#"

        assert isinstance(HEX_COLOR_LENGTH, int)
        assert HEX_COLOR_LENGTH == 7  # Including # prefix

    def test_priority_text_format(self):
        """Test priority text formatting."""
        for _priority, (text, style) in PRIORITY_LEVELS.items():
            # Text should be human-readable
            assert text.replace(" ", "").isalpha() or any(c.isalpha() for c in text)

            # Style should be a valid Rich style (basic check)
            assert isinstance(style, str)

    def test_constants_immutability(self):
        """Test that constants are properly defined as expected types."""
        # These should be the expected types and not accidentally mutable
        assert isinstance(PRIORITY_LEVELS, dict)
        assert isinstance(COLOR_PATTERNS, dict)

        # String constants should be strings
        string_constants = [
            OAUTH_REDIRECT_URI,
            DEFAULT_COLOR_STYLE,
            DEFAULT_STATE_COLOR,
            TEAM_ID_PREFIX,
            HEX_COLOR_PREFIX,
        ]

        for const in string_constants:
            assert isinstance(const, str)
            assert len(const) > 0

        # Integer constants should be integers
        integer_constants = [
            DEFAULT_API_TIMEOUT,
            DEFAULT_CACHE_TTL,
            DEFAULT_ISSUE_LIMIT,
            MAX_ISSUE_LIMIT,
            DEFAULT_LABEL_LIMIT,
            OAUTH_CALLBACK_PORT,
            TEAM_ID_MIN_LENGTH,
            HEX_COLOR_LENGTH,
            LINEAR_API_RATE_LIMIT_WINDOW,
        ]

        for const in integer_constants:
            assert isinstance(const, int)
            assert const > 0

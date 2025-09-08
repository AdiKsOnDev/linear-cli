"""Tests for CLI output formatters."""

from unittest.mock import patch

from rich.text import Text

from linear_cli.cli.formatters import (
    format_datetime,
    format_labels,
    get_priority_text,
    get_state_text,
    print_error,
    print_info,
    print_success,
    print_warning,
    truncate_text,
)


class TestDateTimeFormatting:
    """Test datetime formatting functions."""

    def test_format_datetime_valid_iso(self):
        """Test formatting valid ISO datetime strings."""
        # Test ISO format with Z timezone
        iso_string = "2024-01-15T10:30:00Z"
        result = format_datetime(iso_string)
        assert result == "2024-01-15 10:30"

    def test_format_datetime_with_timezone(self):
        """Test formatting datetime with timezone offset."""
        iso_string = "2024-01-15T10:30:00+02:00"
        result = format_datetime(iso_string)
        assert result == "2024-01-15 08:30"  # Adjusted to UTC

    def test_format_datetime_none(self):
        """Test formatting None datetime."""
        result = format_datetime(None)
        assert result == ""

    def test_format_datetime_empty_string(self):
        """Test formatting empty datetime string."""
        result = format_datetime("")
        assert result == ""

    def test_format_datetime_invalid(self):
        """Test formatting invalid datetime string."""
        result = format_datetime("invalid-date")
        assert result == "invalid-date"


class TestPriorityFormatting:
    """Test priority formatting functions."""

    def test_get_priority_text_valid(self):
        """Test getting priority text for valid priorities."""
        result = get_priority_text(1)
        assert isinstance(result, Text)

        result = get_priority_text(4)
        assert isinstance(result, Text)

    def test_get_priority_text_none(self):
        """Test getting priority text for None."""
        result = get_priority_text(None)
        assert isinstance(result, Text)

    def test_get_priority_text_invalid(self):
        """Test getting priority text for invalid priority."""
        result = get_priority_text(99)
        assert isinstance(result, Text)

    def test_get_priority_text_zero(self):
        """Test getting priority text for zero priority."""
        result = get_priority_text(0)
        assert isinstance(result, Text)


class TestStateFormatting:
    """Test state formatting functions."""

    def test_get_state_text_valid(self):
        """Test getting state text for valid state."""
        state = {"name": "In Progress", "type": "started", "color": "#ff6900"}
        result = get_state_text(state)
        assert isinstance(result, Text)

    def test_get_state_text_none(self):
        """Test getting state text for None state."""
        result = get_state_text(None)
        assert isinstance(result, Text)
        assert "Unknown" in str(result)

    def test_get_state_text_empty(self):
        """Test getting state text for empty state dict."""
        result = get_state_text({})
        assert isinstance(result, Text)

    def test_get_state_text_minimal(self):
        """Test getting state text with minimal state data."""
        state = {"name": "Todo"}
        result = get_state_text(state)
        assert isinstance(result, Text)


class TestLabelFormatting:
    """Test label formatting functions."""

    def test_format_labels_with_labels(self):
        """Test formatting labels with valid label data."""
        labels = [
            {"name": "bug", "color": "#d73a4a"},
            {"name": "urgent", "color": "#fbca04"},
        ]
        result = format_labels(labels)
        assert isinstance(result, str)
        assert "bug" in result
        assert "urgent" in result

    def test_format_labels_empty(self):
        """Test formatting empty labels."""
        result = format_labels([])
        assert result == ""

    def test_format_labels_none(self):
        """Test formatting None labels."""
        result = format_labels(None)
        assert result == ""

    def test_format_labels_single(self):
        """Test formatting single label."""
        labels = [{"name": "feature", "color": "#0e8a16"}]
        result = format_labels(labels)
        assert isinstance(result, str)
        assert "feature" in result


class TestTextUtilities:
    """Test text utility functions."""

    def test_truncate_text_short(self):
        """Test truncating text shorter than limit."""
        text = "Short text"
        result = truncate_text(text, max_length=20)
        assert result == "Short text"

    def test_truncate_text_long(self):
        """Test truncating text longer than limit."""
        text = "This is a very long text that should be truncated"
        result = truncate_text(text, max_length=20)
        assert len(result) <= 20
        assert result.endswith("...")

    def test_truncate_text_none(self):
        """Test truncating None text."""
        result = truncate_text(None, max_length=20)
        assert result == ""

    def test_truncate_text_empty(self):
        """Test truncating empty text."""
        result = truncate_text("", max_length=20)
        assert result == ""

    def test_truncate_text_exact_length(self):
        """Test truncating text at exact max length."""
        text = "Exactly twenty chars"  # 20 characters
        result = truncate_text(text, max_length=20)
        assert result == text

    def test_truncate_text_default_length(self):
        """Test truncating with default max length."""
        text = "This is a very long text that exceeds the default maximum length limit"
        result = truncate_text(text)
        # Default should be 50
        assert len(result) <= 50


class TestPrintFunctions:
    """Test printing utility functions."""

    @patch("linear_cli.cli.formatters.console")
    def test_print_success(self, mock_console):
        """Test success message printing."""
        print_success("Operation completed")
        mock_console.print.assert_called_once()

        # Check that it was called with appropriate styling
        call_args = mock_console.print.call_args
        assert "Operation completed" in str(call_args)

    @patch("linear_cli.cli.formatters.console")
    def test_print_error(self, mock_console):
        """Test error message printing."""
        print_error("Something went wrong")
        mock_console.print.assert_called_once()

        call_args = mock_console.print.call_args
        assert "Something went wrong" in str(call_args)

    @patch("linear_cli.cli.formatters.console")
    def test_print_warning(self, mock_console):
        """Test warning message printing."""
        print_warning("This is a warning")
        mock_console.print.assert_called_once()

        call_args = mock_console.print.call_args
        assert "This is a warning" in str(call_args)

    @patch("linear_cli.cli.formatters.console")
    def test_print_info(self, mock_console):
        """Test info message printing."""
        print_info("Information message")
        mock_console.print.assert_called_once()

        call_args = mock_console.print.call_args
        assert "Information message" in str(call_args)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_format_datetime_with_microseconds(self):
        """Test formatting datetime with microseconds."""
        iso_string = "2024-01-15T10:30:00.123456Z"
        result = format_datetime(iso_string)
        # Should handle microseconds gracefully
        assert isinstance(result, str)

    def test_get_state_text_malformed_state(self):
        """Test getting state text for malformed state."""
        malformed_states = [
            {"invalid_key": "value"},
            {"name": None},
            {"name": ""},
        ]

        for state in malformed_states:
            result = get_state_text(state)
            assert isinstance(result, Text)

    def test_format_labels_malformed_labels(self):
        """Test formatting malformed label data."""
        malformed_labels = [
            [{"name": None}],
            [{"invalid_key": "value"}],
            [{}],
            "not_a_list",
            123,
        ]

        for labels in malformed_labels:
            try:
                result = format_labels(labels)
                assert isinstance(result, str)
            except (TypeError, AttributeError):
                # Some malformed inputs might raise exceptions
                pass

    def test_truncate_text_negative_length(self):
        """Test truncating with negative max length."""
        text = "Test text"
        result = truncate_text(text, max_length=-5)
        # Should handle negative length gracefully
        assert isinstance(result, str)

    def test_truncate_text_zero_length(self):
        """Test truncating with zero max length."""
        text = "Test text"
        result = truncate_text(text, max_length=0)
        assert isinstance(result, str)

    def test_get_priority_text_negative(self):
        """Test priority text for negative priority."""
        result = get_priority_text(-1)
        assert isinstance(result, Text)

    def test_get_priority_text_float(self):
        """Test priority text for float priority (should handle type conversion)."""
        result = get_priority_text(2.5)
        assert isinstance(result, Text)

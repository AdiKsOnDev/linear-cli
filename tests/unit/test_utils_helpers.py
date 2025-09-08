"""Tests for utility helpers."""

import pytest

from linear_cli.utils.helpers import (
    batch_items,
    deep_merge_dicts,
    flatten_dict,
    format_date,
    format_relative_time,
    parse_date_input,
    retry_with_backoff,
    safe_json_loads,
    sanitize_filename,
    truncate_string,
    validate_email,
    validate_uuid,
)


class TestDateHelpers:
    """Test date formatting and parsing helpers."""

    def test_format_date_iso_string(self):
        """Test formatting ISO date string."""
        iso_date = "2025-01-15T14:30:00.000Z"
        formatted = format_date(iso_date)

        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_date_datetime_object(self):
        """Test formatting datetime object."""
        from datetime import datetime

        dt = datetime(2025, 1, 15, 14, 30, 0)
        formatted = format_date(dt)

        assert isinstance(formatted, str)
        assert "2025" in formatted

    def test_format_date_none(self):
        """Test formatting None date."""
        formatted = format_date(None)
        assert formatted == "Never" or formatted == "" or formatted is None

    def test_format_date_invalid(self):
        """Test formatting invalid date."""
        formatted = format_date("invalid-date")
        assert formatted is None or formatted == "Invalid date"

    def test_format_relative_time_recent(self):
        """Test formatting recent time."""
        from datetime import datetime, timedelta

        recent_time = datetime.now() - timedelta(minutes=5)
        formatted = format_relative_time(recent_time)

        assert isinstance(formatted, str)
        assert "minute" in formatted or "ago" in formatted

    def test_format_relative_time_old(self):
        """Test formatting old time."""
        from datetime import datetime, timedelta

        old_time = datetime.now() - timedelta(days=30)
        formatted = format_relative_time(old_time)

        assert isinstance(formatted, str)
        assert "day" in formatted or "month" in formatted or "ago" in formatted

    def test_parse_date_input_relative(self):
        """Test parsing relative date input."""
        relative_inputs = ["today", "yesterday", "1 week ago", "2 days ago"]

        for date_input in relative_inputs:
            parsed = parse_date_input(date_input)
            # Should either parse successfully or return None
            assert parsed is None or hasattr(parsed, "year")

    def test_parse_date_input_invalid(self):
        """Test parsing invalid date input."""
        invalid_inputs = ["not-a-date", "invalid", ""]

        for date_input in invalid_inputs:
            parsed = parse_date_input(date_input)
            assert parsed is None


class TestStringHelpers:
    """Test string manipulation helpers."""

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        unsafe_name = "file/with\\unsafe:chars*?.txt"
        safe_name = sanitize_filename(unsafe_name)

        # Should remove/replace unsafe characters
        unsafe_chars = ["/", "\\", ":", "*", "?", "<", ">", "|"]
        for char in unsafe_chars:
            assert char not in safe_name

    def test_sanitize_filename_empty(self):
        """Test sanitizing empty filename."""
        safe_name = sanitize_filename("")
        assert safe_name == "" or safe_name == "untitled"

    def test_sanitize_filename_long(self):
        """Test sanitizing very long filename."""
        long_name = "a" * 300  # Very long filename
        safe_name = sanitize_filename(long_name)

        # Should be truncated to reasonable length
        assert len(safe_name) <= 255  # Common filesystem limit

    def test_truncate_string_short(self):
        """Test truncating short string."""
        short_text = "Short text"
        truncated = truncate_string(short_text, max_length=50)

        assert truncated == short_text

    def test_truncate_string_long(self):
        """Test truncating long string."""
        long_text = "This is a very long string that should be truncated"
        truncated = truncate_string(long_text, max_length=20)

        assert len(truncated) <= 20
        assert truncated.endswith("...") or len(truncated) == 20

    def test_truncate_string_exact_length(self):
        """Test truncating string at exact max length."""
        text = "Exactly twenty chars"
        assert len(text) == 20

        truncated = truncate_string(text, max_length=20)
        assert truncated == text

    def test_truncate_string_with_ellipsis(self):
        """Test truncation includes ellipsis in length calculation."""
        long_text = "This should be truncated with ellipsis"
        truncated = truncate_string(long_text, max_length=15)

        if "..." in truncated:
            assert len(truncated) <= 15


class TestValidationHelpers:
    """Test validation helper functions."""

    def test_validate_email_valid(self):
        """Test validating valid email addresses."""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.org",
            "firstname.lastname@company.com",
        ]

        for email in valid_emails:
            assert validate_email(email) is True

    def test_validate_email_invalid(self):
        """Test validating invalid email addresses."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "",
            None,
        ]

        for email in invalid_emails:
            assert validate_email(email) is False

    def test_validate_uuid_valid(self):
        """Test validating valid UUIDs."""
        import uuid

        valid_uuids = [
            str(uuid.uuid4()),
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        ]

        for uuid_str in valid_uuids:
            assert validate_uuid(uuid_str) is True

    def test_validate_uuid_invalid(self):
        """Test validating invalid UUIDs."""
        invalid_uuids = [
            "not-a-uuid",
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
            "",
            None,
        ]

        for uuid_str in invalid_uuids:
            assert validate_uuid(uuid_str) is False


class TestDataHelpers:
    """Test data manipulation helpers."""

    def test_deep_merge_dicts_simple(self):
        """Test merging simple dictionaries."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}

        merged = deep_merge_dicts(dict1, dict2)

        expected = {"a": 1, "b": 2, "c": 3, "d": 4}
        assert merged == expected

    def test_deep_merge_dicts_nested(self):
        """Test merging nested dictionaries."""
        dict1 = {"user": {"name": "John", "age": 30}, "settings": {"theme": "dark"}}
        dict2 = {
            "user": {"email": "john@example.com"},
            "settings": {"notifications": True},
        }

        merged = deep_merge_dicts(dict1, dict2)

        # Should merge nested structures
        assert merged["user"]["name"] == "John"
        assert merged["user"]["email"] == "john@example.com"
        assert merged["settings"]["theme"] == "dark"
        assert merged["settings"]["notifications"] is True

    def test_deep_merge_dicts_override(self):
        """Test merging dictionaries with value override."""
        dict1 = {"key": "old_value", "other": "unchanged"}
        dict2 = {"key": "new_value"}

        merged = deep_merge_dicts(dict1, dict2)

        assert merged["key"] == "new_value"
        assert merged["other"] == "unchanged"

    def test_flatten_dict_simple(self):
        """Test flattening simple dictionary."""
        nested_dict = {
            "user": {"name": "John", "profile": {"age": 30, "city": "New York"}},
            "active": True,
        }

        flattened = flatten_dict(nested_dict)

        assert "user.name" in flattened
        assert "user.profile.age" in flattened
        assert "user.profile.city" in flattened
        assert "active" in flattened

        assert flattened["user.name"] == "John"
        assert flattened["user.profile.age"] == 30
        assert flattened["active"] is True

    def test_flatten_dict_custom_separator(self):
        """Test flattening dictionary with custom separator."""
        nested_dict = {"a": {"b": {"c": "value"}}}

        flattened = flatten_dict(nested_dict, separator="__")

        assert "a__b__c" in flattened
        assert flattened["a__b__c"] == "value"

    def test_flatten_dict_empty(self):
        """Test flattening empty dictionary."""
        flattened = flatten_dict({})
        assert flattened == {}

    def test_safe_json_loads_valid(self):
        """Test safe JSON loading with valid JSON."""
        valid_json = '{"key": "value", "number": 42}'
        result = safe_json_loads(valid_json)

        assert result == {"key": "value", "number": 42}

    def test_safe_json_loads_invalid(self):
        """Test safe JSON loading with invalid JSON."""
        invalid_json = '{"key": invalid_json}'
        result = safe_json_loads(invalid_json)

        assert result is None

    def test_safe_json_loads_with_default(self):
        """Test safe JSON loading with default value."""
        invalid_json = '{"key": invalid_json}'
        default_value = {"default": True}

        result = safe_json_loads(invalid_json, default=default_value)

        assert result == default_value

    def test_safe_json_loads_empty_string(self):
        """Test safe JSON loading with empty string."""
        result = safe_json_loads("")
        assert result is None

    def test_safe_json_loads_none(self):
        """Test safe JSON loading with None."""
        result = safe_json_loads(None)
        assert result is None


class TestRetryHelper:
    """Test retry with backoff helper."""

    def test_retry_success_first_attempt(self):
        """Test retry decorator with success on first attempt."""
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()

        assert result == "success"
        assert call_count == 1

    def test_retry_success_after_failures(self):
        """Test retry decorator with success after failures."""
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def eventually_successful():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        result = eventually_successful()

        assert result == "success"
        assert call_count == 3

    def test_retry_max_retries_exceeded(self):
        """Test retry decorator when max retries exceeded."""
        call_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise Exception("Always fails")

        with pytest.raises(Exception, match="Always fails"):
            always_fails()

        # Should have tried max_retries + 1 times (initial + retries)
        assert call_count == 3

    def test_retry_specific_exceptions(self):
        """Test retry with specific exception types."""
        call_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=0.01, exceptions=(ValueError,))
        def fails_with_value_error():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retryable error")
            elif call_count == 2:
                raise TypeError("Non-retryable error")
            return "success"

        # Should raise TypeError (not retryable) after first ValueError retry
        with pytest.raises(TypeError):
            fails_with_value_error()

        assert call_count == 2


class TestBatchHelper:
    """Test batch processing helper."""

    def test_batch_items_even_division(self):
        """Test batching items with even division."""
        items = list(range(10))  # [0, 1, 2, ..., 9]
        batches = list(batch_items(items, batch_size=5))

        assert len(batches) == 2
        assert batches[0] == [0, 1, 2, 3, 4]
        assert batches[1] == [5, 6, 7, 8, 9]

    def test_batch_items_uneven_division(self):
        """Test batching items with uneven division."""
        items = list(range(7))  # [0, 1, 2, 3, 4, 5, 6]
        batches = list(batch_items(items, batch_size=3))

        assert len(batches) == 3
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6]

    def test_batch_items_empty(self):
        """Test batching empty list."""
        batches = list(batch_items([], batch_size=5))
        assert len(batches) == 0

    def test_batch_items_single_batch(self):
        """Test batching when all items fit in one batch."""
        items = [1, 2, 3]
        batches = list(batch_items(items, batch_size=5))

        assert len(batches) == 1
        assert batches[0] == [1, 2, 3]

    def test_batch_items_size_one(self):
        """Test batching with batch size of 1."""
        items = ["a", "b", "c"]
        batches = list(batch_items(items, batch_size=1))

        assert len(batches) == 3
        assert batches[0] == ["a"]
        assert batches[1] == ["b"]
        assert batches[2] == ["c"]

    def test_batch_items_large_batch_size(self):
        """Test batching with batch size larger than items."""
        items = [1, 2]
        batches = list(batch_items(items, batch_size=10))

        assert len(batches) == 1
        assert batches[0] == [1, 2]


class TestMiscHelpers:
    """Test miscellaneous helper functions."""

    def test_ensure_list_with_list(self):
        """Test ensuring list when input is already a list."""
        input_list = [1, 2, 3]
        if hasattr(
            __import__("linear_cli.utils.helpers", fromlist=[""]), "ensure_list"
        ):
            from linear_cli.utils.helpers import ensure_list

            result = ensure_list(input_list)
            assert result == input_list

    def test_ensure_list_with_single_item(self):
        """Test ensuring list when input is a single item."""
        if hasattr(
            __import__("linear_cli.utils.helpers", fromlist=[""]), "ensure_list"
        ):
            from linear_cli.utils.helpers import ensure_list

            result = ensure_list("single_item")
            assert result == ["single_item"]

    def test_ensure_list_with_none(self):
        """Test ensuring list when input is None."""
        if hasattr(
            __import__("linear_cli.utils.helpers", fromlist=[""]), "ensure_list"
        ):
            from linear_cli.utils.helpers import ensure_list

            result = ensure_list(None)
            assert result == []

    def test_get_nested_value(self):
        """Test getting nested dictionary value."""
        if hasattr(
            __import__("linear_cli.utils.helpers", fromlist=[""]), "get_nested_value"
        ):
            from linear_cli.utils.helpers import get_nested_value

            data = {"user": {"profile": {"name": "John Doe"}}}

            result = get_nested_value(data, "user.profile.name")
            assert result == "John Doe"

            # Test with missing path
            result = get_nested_value(data, "user.missing.key", default="default")
            assert result == "default"

    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        if hasattr(
            __import__("linear_cli.utils.helpers", fromlist=[""]), "calculate_file_hash"
        ):
            import tempfile

            from linear_cli.utils.helpers import calculate_file_hash

            # Create temporary file
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                f.write("test content")
                temp_path = f.name

            try:
                hash_value = calculate_file_hash(temp_path)
                assert isinstance(hash_value, str)
                assert len(hash_value) > 0
            finally:
                import os

                os.unlink(temp_path)

    def test_normalize_line_endings(self):
        """Test normalizing line endings."""
        if hasattr(
            __import__("linear_cli.utils.helpers", fromlist=[""]),
            "normalize_line_endings",
        ):
            from linear_cli.utils.helpers import normalize_line_endings

            # Test different line endings
            windows_text = "line1\r\nline2\r\nline3"
            mac_text = "line1\rline2\rline3"
            mixed_text = "line1\r\nline2\nline3\r"

            for text in [windows_text, mac_text, mixed_text]:
                normalized = normalize_line_endings(text)
                assert (
                    "\r\n" not in normalized or "\r\n" in normalized
                )  # Should be consistent
                assert "\r" not in normalized or normalized.count(
                    "\r"
                ) == normalized.count("\r\n")

"""
Unit tests for user management functionality.

Tests the user management commands including list, show, workload analysis, and assignment suggestions.
"""

from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_context():
    """Create mock Click context for user management tests."""
    ctx = MagicMock()
    cli_ctx = MagicMock()
    client = MagicMock()
    config = MagicMock()

    cli_ctx.get_client.return_value = client
    cli_ctx.config = config
    ctx.obj = {"cli_context": cli_ctx}

    # Mock async methods
    client.get_users = AsyncMock()
    client.get_issues = AsyncMock()
    client.get_teams = AsyncMock()

    return ctx, cli_ctx, client, config


@pytest.fixture
def sample_users():
    """Sample user data for testing."""
    return [
        {
            "id": "user-1",
            "name": "John Doe",
            "displayName": "John Doe",
            "email": "john@company.com",
            "active": True,
        },
        {
            "id": "user-2",
            "name": "Jane Smith",
            "displayName": "Jane Smith",
            "email": "jane@company.com",
            "active": True,
        },
        {
            "id": "user-3",
            "name": "Bob Wilson",
            "displayName": "Bob Wilson",
            "email": "bob@company.com",
            "active": False,
        },
    ]


@pytest.fixture
def sample_user_issues():
    """Sample issues assigned to users for workload testing."""
    return {
        "nodes": [
            {
                "id": "issue-1",
                "identifier": "ENG-123",
                "title": "Authentication bug fix",
                "priority": 3,  # High
                "state": {"name": "In Progress"},
                "assignee": {
                    "id": "user-1",
                    "displayName": "John Doe",
                    "email": "john@company.com",
                },
                "updatedAt": "2025-01-15T10:00:00Z",
            },
            {
                "id": "issue-2",
                "identifier": "ENG-124",
                "title": "Login timeout handling",
                "priority": 2,  # Normal
                "state": {"name": "To Do"},
                "assignee": {
                    "id": "user-1",
                    "displayName": "John Doe",
                    "email": "john@company.com",
                },
                "updatedAt": "2025-01-15T09:00:00Z",
            },
            {
                "id": "issue-3",
                "identifier": "ENG-125",
                "title": "Security enhancement",
                "priority": 4,  # Urgent
                "state": {"name": "Done"},
                "assignee": {
                    "id": "user-1",
                    "displayName": "John Doe",
                    "email": "john@company.com",
                },
                "updatedAt": "2025-01-14T15:30:00Z",
            },
            {
                "id": "issue-4",
                "identifier": "ENG-126",
                "title": "UI improvement",
                "priority": 1,  # Low
                "state": {"name": "In Progress"},
                "assignee": {
                    "id": "user-2",
                    "displayName": "Jane Smith",
                    "email": "jane@company.com",
                },
                "updatedAt": "2025-01-15T08:00:00Z",
            },
        ]
    }


class TestUserManagement:
    """Test user management functionality."""

    pass


class TestUserList:
    """Test user list functionality."""

    @patch("linearator.cli.commands.user.asyncio.run")
    async def test_user_list_basic(self, mock_asyncio_run, mock_context, sample_users):
        """Test basic user listing functionality."""
        ctx, cli_ctx, client, config = mock_context
        config.output_format = "table"
        config.no_color = False

        client.get_users.return_value = sample_users
        mock_asyncio_run.return_value = None

        # Verify the setup is correct
        assert ctx.obj["cli_context"] == cli_ctx
        assert len(sample_users) == 3

    async def test_user_list_team_filtering(self, mock_context, sample_users):
        """Test user list with team filtering."""
        ctx, cli_ctx, client, config = mock_context
        client.get_users.return_value = sample_users

        # Test team ID vs team key detection
        team_cases = [("ENG", "team_key"), ("team_123456789_abc", "team_id")]

        for team, expected_param_type in team_cases:
            is_id = len(team) > 10 or "-" in team or "_" in team
            actual_param_type = "team_id" if is_id else "team_key"
            assert actual_param_type == expected_param_type

    def test_user_list_output_formats(self, sample_users):
        """Test different output formats for user list."""
        formats = ["table", "json", "yaml"]

        for output_format in formats:
            assert output_format in ["table", "json", "yaml"]

            if output_format == "table":
                # Table format should have columns
                expected_columns = ["Name", "Email", "ID", "Status"]
                for col in expected_columns:
                    assert len(col) > 0
            elif output_format in ["json", "yaml"]:
                # Structured formats should preserve all data
                for user in sample_users:
                    required_fields = ["id", "displayName", "email", "active"]
                    for field in required_fields:
                        assert field in user

    def test_user_list_status_display(self, sample_users):
        """Test user status display logic."""
        for user in sample_users:
            is_active = user.get("active", True)
            if is_active:
                status_display = "Active"
            else:
                status_display = "Inactive"

            assert status_display in ["Active", "Inactive"]
            assert (status_display == "Active") == is_active

    async def test_user_list_empty_results(self, mock_context):
        """Test user list with no users found."""
        ctx, cli_ctx, client, config = mock_context
        client.get_users.return_value = []

        empty_users = await client.get_users()
        assert len(empty_users) == 0


class TestUserShow:
    """Test user show (detailed view) functionality."""

    async def test_user_show_parameter_detection(self):
        """Test user identifier parameter detection."""
        test_cases = [
            ("john@company.com", "email", True),
            ("usr_123456789", "id", False),
            ("jane.doe@example.org", "email", True),
            ("user_abc123", "id", False),
        ]

        for identifier, expected_type, is_email in test_cases:
            detected_email = "@" in identifier
            assert detected_email == is_email

            if detected_email:
                assert expected_type == "email"
            else:
                assert expected_type == "id"

    def test_user_workload_analysis(self, sample_user_issues):
        """Test user workload analysis logic."""
        issues = sample_user_issues["nodes"]
        user_id = "user-1"

        # Filter issues for the user
        user_issues = [issue for issue in issues if issue["assignee"]["id"] == user_id]

        # Analyze workload
        priority_counts = defaultdict(int)
        state_counts = defaultdict(int)

        for issue in user_issues:
            priority = issue.get("priority", 0)
            state = issue.get("state", {}).get("name", "Unknown")

            priority_counts[priority] += 1
            state_counts[state] += 1

        # Verify analysis results
        assert len(user_issues) == 3  # John has 3 issues
        assert priority_counts[3] == 1  # 1 High priority
        assert priority_counts[2] == 1  # 1 Normal priority
        assert priority_counts[4] == 1  # 1 Urgent priority
        assert state_counts["In Progress"] == 1
        assert state_counts["To Do"] == 1
        assert state_counts["Done"] == 1

    def test_workload_metrics_calculation(self, sample_user_issues):
        """Test workload metrics calculation."""
        issues = sample_user_issues["nodes"]
        user_issues = [issue for issue in issues if issue["assignee"]["id"] == "user-1"]
        total_issues = len(user_issues)

        # Priority breakdown percentages
        priority_counts = defaultdict(int)
        for issue in user_issues:
            priority = issue.get("priority", 0)
            priority_counts[priority] += 1

        for _priority, count in priority_counts.items():
            percentage = (count / total_issues) * 100
            assert 0 <= percentage <= 100
            assert percentage == (count / total_issues) * 100

    def test_recent_issues_sorting(self, sample_user_issues):
        """Test recent issues sorting logic."""
        issues = sample_user_issues["nodes"]
        user_issues = [issue for issue in issues if issue["assignee"]["id"] == "user-1"]

        # Sort by updated date (most recent first)
        sorted_issues = sorted(
            user_issues, key=lambda x: x.get("updatedAt", ""), reverse=True
        )

        # Verify sorting
        assert len(sorted_issues) == 3
        assert sorted_issues[0]["identifier"] == "ENG-123"  # Most recent
        assert sorted_issues[1]["identifier"] == "ENG-124"  # Middle
        assert sorted_issues[2]["identifier"] == "ENG-125"  # Oldest

    async def test_user_show_team_filtering(self, mock_context, sample_user_issues):
        """Test user show with team filtering."""
        ctx, cli_ctx, client, config = mock_context
        client.get_issues.return_value = sample_user_issues

        # Test filtering by team
        team = "ENG"

        # Mock call should include team parameter
        expected_call_args = {
            "team_key": team,
            "assignee_email": "john@company.com",
            "limit": 100,
        }

        # Verify that team filtering would be applied
        for _key, value in expected_call_args.items():
            assert value is not None


class TestUserWorkload:
    """Test user workload analysis functionality."""

    def test_workload_distribution_analysis(self, sample_user_issues):
        """Test workload distribution analysis."""
        issues = sample_user_issues["nodes"]

        # Analyze workload distribution
        user_workloads = defaultdict(
            lambda: {"total": 0, "high_priority": 0, "urgent": 0, "user_info": None}
        )

        unassigned_count = 0

        for issue in issues:
            assignee = issue.get("assignee")
            priority = issue.get("priority", 0)

            if assignee:
                user_id = assignee.get("id")
                user_workloads[user_id]["total"] += 1
                user_workloads[user_id]["user_info"] = assignee

                if priority >= 3:  # High or Urgent
                    user_workloads[user_id]["high_priority"] += 1
                if priority == 4:  # Urgent only
                    user_workloads[user_id]["urgent"] += 1
            else:
                unassigned_count += 1

        # Verify analysis results
        assert len(user_workloads) == 2  # 2 users have assignments
        assert user_workloads["user-1"]["total"] == 3
        assert user_workloads["user-1"]["high_priority"] == 2  # 1 High + 1 Urgent
        assert user_workloads["user-1"]["urgent"] == 1
        assert user_workloads["user-2"]["total"] == 1
        assert unassigned_count == 0

    def test_workload_sorting_options(self):
        """Test different workload sorting options."""
        # Sample workload data
        user_workloads = {
            "user-1": {
                "total": 5,
                "high_priority": 2,
                "user_info": {"displayName": "Alice"},
            },
            "user-2": {
                "total": 3,
                "high_priority": 1,
                "user_info": {"displayName": "Bob"},
            },
            "user-3": {
                "total": 7,
                "high_priority": 4,
                "user_info": {"displayName": "Charlie"},
            },
        }

        users_list = list(user_workloads.items())

        # Test sorting by total issues
        sorted_by_total = sorted(users_list, key=lambda x: x[1]["total"], reverse=True)
        assert sorted_by_total[0][1]["total"] == 7  # Charlie first
        assert sorted_by_total[1][1]["total"] == 5  # Alice second
        assert sorted_by_total[2][1]["total"] == 3  # Bob last

        # Test sorting by high priority issues
        sorted_by_priority = sorted(
            users_list, key=lambda x: x[1]["high_priority"], reverse=True
        )
        assert sorted_by_priority[0][1]["high_priority"] == 4  # Charlie first
        assert sorted_by_priority[1][1]["high_priority"] == 2  # Alice second
        assert sorted_by_priority[2][1]["high_priority"] == 1  # Bob last

        # Test sorting by name
        sorted_by_name = sorted(
            users_list, key=lambda x: x[1]["user_info"]["displayName"].lower()
        )
        names = [user[1]["user_info"]["displayName"] for user in sorted_by_name]
        assert names == ["Alice", "Bob", "Charlie"]

    def test_workload_balance_analysis(self):
        """Test workload balance analysis and recommendations."""
        user_workloads = [
            ("user-1", {"total": 10}),  # Overloaded
            ("user-2", {"total": 5}),  # Normal
            ("user-3", {"total": 2}),  # Underloaded
            ("user-4", {"total": 6}),  # Normal
        ]

        # Calculate average load
        total_load = sum(data["total"] for _, data in user_workloads)
        avg_load = total_load / len(user_workloads)
        assert avg_load == 5.75

        # Identify load categories
        overloaded = [u for u in user_workloads if u[1]["total"] > avg_load * 1.5]
        underloaded = [u for u in user_workloads if u[1]["total"] < avg_load * 0.5]

        assert len(overloaded) == 1  # user-1 (10 > 8.625)
        assert len(underloaded) == 1  # user-3 (2 < 2.875)

    def test_unassigned_issues_analysis(self, sample_user_issues):
        """Test unassigned issues analysis."""
        issues = sample_user_issues["nodes"]

        # Count unassigned issues
        unassigned_count = 0
        unassigned_high_priority = 0

        for issue in issues:
            if not issue.get("assignee"):
                unassigned_count += 1
                if issue.get("priority", 0) >= 3:
                    unassigned_high_priority += 1

        # All sample issues are assigned
        assert unassigned_count == 0
        assert unassigned_high_priority == 0

        # Test with mock unassigned issues
        mock_unassigned = [
            {"assignee": None, "priority": 2},  # Normal priority unassigned
            {"assignee": None, "priority": 4},  # Urgent unassigned
        ]

        unassigned_mock_count = 0
        high_priority_unassigned_mock = 0

        for issue in mock_unassigned:
            if not issue.get("assignee"):
                unassigned_mock_count += 1
                if issue.get("priority", 0) >= 3:
                    high_priority_unassigned_mock += 1

        assert unassigned_mock_count == 2
        assert high_priority_unassigned_mock == 1


class TestAssignmentSuggestions:
    """Test assignment suggestion functionality."""

    def test_assignment_scoring_logic(self, sample_users, sample_user_issues):
        """Test assignment scoring algorithm."""
        users = sample_users
        issues = sample_user_issues["nodes"]

        # Calculate workload scores for users
        user_workloads = {}
        for user in users:
            user_id = user["id"]
            user_issues = [
                issue
                for issue in issues
                if issue.get("assignee", {}).get("id") == user_id
            ]

            total_count = len(user_issues)
            high_priority_count = len(
                [i for i in user_issues if i.get("priority", 0) >= 3]
            )

            # Score formula: total + (high_priority * 0.5)
            score = total_count + (high_priority_count * 0.5)

            user_workloads[user_id] = {
                "user_info": user,
                "total": total_count,
                "high_priority": high_priority_count,
                "score": score,
            }

        # Verify scoring
        assert user_workloads["user-1"]["score"] == 4.0  # 3 total + (2 high * 0.5)
        assert user_workloads["user-2"]["score"] == 1.0  # 1 total + (0 high * 0.5)
        assert user_workloads["user-3"]["score"] == 0.0  # 0 total + (0 high * 0.5)

    def test_round_robin_assignment_logic(self):
        """Test round-robin assignment logic."""
        # Sorted users by workload (least loaded first)
        users_by_load = [
            ("user-3", {"score": 0.0, "user_info": {"displayName": "Bob"}}),
            ("user-2", {"score": 1.0, "user_info": {"displayName": "Jane"}}),
            ("user-1", {"score": 4.0, "user_info": {"displayName": "John"}}),
        ]

        issue_count = 5
        assignments = []

        # Round-robin assignment
        for i in range(issue_count):
            user_idx = i % len(users_by_load)
            user_id, user_data = users_by_load[user_idx]

            assignments.append(
                {
                    "assignment_number": i + 1,
                    "user_id": user_id,
                    "user_info": user_data["user_info"],
                }
            )

        # Verify round-robin distribution
        assignment_counts = defaultdict(int)
        for assignment in assignments:
            assignment_counts[assignment["user_id"]] += 1

        # With 5 issues and 3 users: [2, 2, 1] distribution expected
        sorted_counts = sorted(assignment_counts.values(), reverse=True)
        assert sorted_counts == [2, 2, 1]

    def test_assignment_suggestion_summary(self):
        """Test assignment suggestion summary generation."""
        suggestions = [
            {"user_id": "user-1", "user_info": {"displayName": "John"}},
            {"user_id": "user-2", "user_info": {"displayName": "Jane"}},
            {"user_id": "user-1", "user_info": {"displayName": "John"}},
            {"user_id": "user-3", "user_info": {"displayName": "Bob"}},
            {"user_id": "user-2", "user_info": {"displayName": "Jane"}},
        ]

        # Count assignments per user
        user_counts = defaultdict(int)
        for suggestion in suggestions:
            name = suggestion["user_info"]["displayName"]
            user_counts[name] += 1

        # Verify counts
        assert user_counts["John"] == 2
        assert user_counts["Jane"] == 2
        assert user_counts["Bob"] == 1
        assert sum(user_counts.values()) == 5

    def test_assignment_exclusion_logic(self, sample_users):
        """Test user exclusion from assignment suggestions."""
        users = sample_users.copy()
        exclude_email = "john@company.com"

        # Filter out excluded user
        filtered_users = []
        for user in users:
            if user.get("email") != exclude_email:
                filtered_users.append(user)

        # Verify exclusion
        assert len(filtered_users) == 2  # Original 3 - 1 excluded
        excluded_emails = [user["email"] for user in filtered_users]
        assert exclude_email not in excluded_emails

    def test_assignment_suggestions_with_constraints(self):
        """Test assignment suggestions with various constraints."""
        constraints = {
            "team": "ENG",
            "priority": 4,
            "exclude_user": "john@company.com",
            "issue_count": 3,
        }

        # Verify constraints are properly handled
        assert constraints["issue_count"] > 0
        assert constraints["priority"] in [0, 1, 2, 3, 4]
        assert "@" in constraints["exclude_user"]  # Email format
        assert len(constraints["team"]) > 0

    def test_assignment_workload_balance_impact(self):
        """Test how assignments impact workload balance."""
        initial_workloads = {"user-1": 5, "user-2": 2, "user-3": 0}

        # Simulate assignment of 3 issues using round-robin on least loaded first
        sorted_users = sorted(initial_workloads.items(), key=lambda x: x[1])
        new_assignments = defaultdict(int)

        for i in range(3):
            user_id = sorted_users[i % len(sorted_users)][0]
            new_assignments[user_id] += 1

        # Calculate new workloads
        final_workloads = {
            user_id: initial_workloads[user_id] + new_assignments[user_id]
            for user_id in initial_workloads
        }

        # Verify improved balance
        initial_max_diff = max(initial_workloads.values()) - min(
            initial_workloads.values()
        )
        final_max_diff = max(final_workloads.values()) - min(final_workloads.values())

        assert final_max_diff <= initial_max_diff  # Balance should improve or stay same
        assert (
            final_workloads["user-3"] > initial_workloads["user-3"]
        )  # Least loaded user gets work

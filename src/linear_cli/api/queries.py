"""
GraphQL queries for Linear API.

Contains reusable GraphQL query fragments and common queries.
"""

from typing import Any

# Common fragments
ISSUE_FRAGMENT = """
fragment IssueFields on Issue {
    id
    identifier
    title
    description
    url
    state {
        id
        name
        color
        type
    }
    priority
    estimate
    createdAt
    updatedAt
    completedAt
    canceledAt
    dueDate
    team {
        id
        name
        key
    }
    assignee {
        id
        name
        displayName
        email
    }
    creator {
        id
        name
        displayName
        email
    }
    labels {
        nodes {
            id
            name
            color
        }
    }
    comments {
        nodes {
            id
            body
            createdAt
            user {
                id
                name
                displayName
            }
        }
    }
}
"""

TEAM_FRAGMENT = """
fragment TeamFields on Team {
    id
    name
    key
    description
    private
    issueCount
    members {
        nodes {
            id
        }
    }
    organization {
        id
        name
    }
    states {
        nodes {
            id
            name
            color
            type
            position
        }
    }
    labels {
        nodes {
            id
            name
            color
            description
        }
    }
}
"""

USER_FRAGMENT = """
fragment UserFields on User {
    id
    name
    displayName
    email
    avatarUrl
    isMe
    active
    admin
    createdAt
    updatedAt
}
"""

LABEL_FRAGMENT = """
fragment LabelFields on IssueLabel {
    id
    name
    color
    description
    createdAt
    updatedAt
    team {
        id
        name
        key
    }
    creator {
        id
        name
        displayName
    }
}
"""

# Common queries
GET_VIEWER_QUERY = f"""
query GetViewer {{
    viewer {{
        ...UserFields
        organization {{
            id
            name
            urlKey
            logoUrl
        }}
    }}
}}
{USER_FRAGMENT}
"""

GET_TEAMS_QUERY = f"""
query GetTeams($first: Int, $after: String, $filter: TeamFilter) {{
    teams(first: $first, after: $after, filter: $filter) {{
        pageInfo {{
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }}
        nodes {{
            ...TeamFields
        }}
    }}
}}
{TEAM_FRAGMENT}
"""

GET_TEAM_QUERY = f"""
query GetTeam($id: String!) {{
    team(id: $id) {{
        ...TeamFields
        members {{
            nodes {{
                ...UserFields
            }}
        }}
    }}
}}
{TEAM_FRAGMENT}
{USER_FRAGMENT}
"""

GET_ISSUES_QUERY = f"""
query GetIssues($first: Int, $after: String, $filter: IssueFilter, $orderBy: PaginationOrderBy) {{
    issues(first: $first, after: $after, filter: $filter, orderBy: $orderBy) {{
        pageInfo {{
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }}
        nodes {{
            ...IssueFields
        }}
    }}
}}
{ISSUE_FRAGMENT}
"""

GET_ISSUE_QUERY = f"""
query GetIssue($id: String!) {{
    issue(id: $id) {{
        ...IssueFields
        parent {{
            id
            identifier
            title
        }}
        children {{
            nodes {{
                id
                identifier
                title
                state {{
                    id
                    name
                    type
                }}
            }}
        }}
        project {{
            id
            name
            description
        }}
        cycle {{
            id
            name
            number
        }}
    }}
}}
{ISSUE_FRAGMENT}
"""

SEARCH_ISSUES_QUERY = """
query SearchIssues($term: String!, $first: Int, $after: String, $filter: IssueFilter) {
    searchIssues(term: $term, first: $first, after: $after, filter: $filter) {
        pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }
        nodes {
            id
            identifier
            title
            description
            priority
            priorityLabel
            url
            branchName
            customerTicketCount
            createdAt
            updatedAt
            archivedAt
            autoArchivedAt
            autoClosedAt
            canceledAt
            completedAt
            snoozedUntilAt
            startedAt
            triagedAt
            dueDate
            estimate
            sortOrder
            boardOrder
            subIssueSortOrder
            previousIdentifiers
            creator {
                id
                name
                email
                displayName
                active
            }
            assignee {
                id
                name
                email
                displayName
                active
            }
            team {
                id
                name
                key
            }
            state {
                id
                name
                type
                color
            }
            project {
                id
                name
            }
            cycle {
                id
                name
                number
            }
            labels {
                nodes {
                    id
                    name
                    color
                }
            }
        }
    }
}
"""

GET_LABELS_QUERY = f"""
query GetLabels($first: Int, $after: String, $filter: IssueLabelFilter) {{
    issueLabels(first: $first, after: $after, filter: $filter) {{
        pageInfo {{
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }}
        nodes {{
            ...LabelFields
        }}
    }}
}}
{LABEL_FRAGMENT}
"""

GET_USERS_QUERY = f"""
query GetUsers($first: Int, $after: String, $filter: UserFilter) {{
    users(first: $first, after: $after, filter: $filter) {{
        pageInfo {{
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }}
        nodes {{
            ...UserFields
        }}
    }}
}}
{USER_FRAGMENT}
"""

# Mutation queries
CREATE_ISSUE_MUTATION = f"""
mutation CreateIssue($input: IssueCreateInput!) {{
    issueCreate(input: $input) {{
        success
        issue {{
            ...IssueFields
        }}
    }}
}}
{ISSUE_FRAGMENT}
"""

UPDATE_ISSUE_MUTATION = f"""
mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {{
    issueUpdate(id: $id, input: $input) {{
        success
        issue {{
            ...IssueFields
        }}
    }}
}}
{ISSUE_FRAGMENT}
"""

DELETE_ISSUE_MUTATION = """
mutation DeleteIssue($id: String!) {
    issueArchive(id: $id) {
        success
    }
}
"""

CREATE_LABEL_MUTATION = f"""
mutation CreateLabel($input: IssueLabelCreateInput!) {{
    issueLabelCreate(input: $input) {{
        success
        issueLabel {{
            ...LabelFields
        }}
    }}
}}
{LABEL_FRAGMENT}
"""

UPDATE_LABEL_MUTATION = f"""
mutation UpdateLabel($id: String!, $input: IssueLabelUpdateInput!) {{
    issueLabelUpdate(id: $id, input: $input) {{
        success
        issueLabel {{
            ...LabelFields
        }}
    }}
}}
{LABEL_FRAGMENT}
"""

DELETE_LABEL_MUTATION = """
mutation DeleteLabel($id: String!) {
    issueLabelDelete(id: $id) {
        success
    }
}
"""


# Utility functions for building filter objects
def build_issue_filter(**kwargs: Any) -> dict[str, Any]:
    """Build an IssueFilter object for GraphQL queries."""
    filter_obj = {}

    # Team filtering
    if "team_id" in kwargs:
        filter_obj["team"] = {"id": {"eq": kwargs["team_id"]}}
    elif "team_key" in kwargs:
        filter_obj["team"] = {"key": {"eq": kwargs["team_key"]}}

    # State filtering
    if "state_id" in kwargs:
        filter_obj["state"] = {"id": {"eq": kwargs["state_id"]}}
    elif "state_name" in kwargs:
        filter_obj["state"] = {"name": {"eq": kwargs["state_name"]}}
    elif "state_type" in kwargs:
        filter_obj["state"] = {"type": {"eq": kwargs["state_type"]}}

    # Assignee filtering
    if "assignee_id" in kwargs:
        filter_obj["assignee"] = {"id": {"eq": kwargs["assignee_id"]}}
    elif "assignee_email" in kwargs:
        filter_obj["assignee"] = {"email": {"eq": kwargs["assignee_email"]}}
    elif "unassigned" in kwargs and kwargs["unassigned"]:
        filter_obj["assignee"] = {"null": {"eq": True}}

    # Creator filtering
    if "creator_id" in kwargs:
        filter_obj["creator"] = {"id": {"eq": kwargs["creator_id"]}}

    # Label filtering
    if "labels" in kwargs:
        filter_obj["labels"] = {"some": {"name": {"in": kwargs["labels"]}}}

    # Priority filtering
    if "priority" in kwargs:
        filter_obj["priority"] = {"eq": kwargs["priority"]}

    # Date filtering
    if "created_after" in kwargs:
        filter_obj["createdAt"] = filter_obj.get("createdAt", {})
        filter_obj["createdAt"]["gte"] = kwargs["created_after"]

    if "created_before" in kwargs:
        filter_obj["createdAt"] = filter_obj.get("createdAt", {})
        filter_obj["createdAt"]["lte"] = kwargs["created_before"]

    if "updated_after" in kwargs:
        filter_obj["updatedAt"] = filter_obj.get("updatedAt", {})
        filter_obj["updatedAt"]["gte"] = kwargs["updated_after"]

    if "updated_before" in kwargs:
        filter_obj["updatedAt"] = filter_obj.get("updatedAt", {})
        filter_obj["updatedAt"]["lte"] = kwargs["updated_before"]

    return filter_obj


def build_team_filter(**kwargs: Any) -> dict[str, Any]:
    """Build a TeamFilter object for GraphQL queries."""
    filter_obj = {}

    if "name" in kwargs:
        filter_obj["name"] = {"contains": kwargs["name"]}

    if "key" in kwargs:
        filter_obj["key"] = {"eq": kwargs["key"]}

    if "private" in kwargs:
        filter_obj["private"] = {"eq": kwargs["private"]}

    return filter_obj


def build_user_filter(**kwargs: Any) -> dict[str, Any]:
    """Build a UserFilter object for GraphQL queries."""
    filter_obj = {}

    if "name" in kwargs:
        filter_obj["name"] = {"contains": kwargs["name"]}

    if "email" in kwargs:
        filter_obj["email"] = {"contains": kwargs["email"]}

    if "active" in kwargs:
        filter_obj["active"] = {"eq": kwargs["active"]}

    if "admin" in kwargs:
        filter_obj["admin"] = {"eq": kwargs["admin"]}

    return filter_obj


# Project queries
GET_PROJECTS_QUERY = """
query GetProjects($first: Int, $after: String) {
    projects(first: $first, after: $after) {
        pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }
        nodes {
            id
            name
            description
            url
            state
            health
            progress
            startDate
            targetDate
            createdAt
            updatedAt
            creator {
                id
                name
                displayName
                email
            }
            lead {
                id
                name
                displayName
                email
            }
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
            members {
                nodes {
                    id
                    name
                    displayName
                    email
                }
            }
        }
    }
}
"""

GET_PROJECT_QUERY = """
query GetProject($id: String!) {
    project(id: $id) {
        id
        name
        description
        url
        state
        health
        progress
        startDate
        targetDate
        createdAt
        updatedAt
        creator {
            id
            name
            displayName
            email
        }
        lead {
            id
            name
            displayName
            email
        }
        teams {
            nodes {
                id
                name
                key
            }
        }
        members {
            nodes {
                id
                name
                displayName
                email
            }
        }
    }
}
"""

CREATE_PROJECT_UPDATE_MUTATION = """
mutation CreateProjectUpdate($input: ProjectUpdateCreateInput!) {
    projectUpdateCreate(input: $input) {
        success
        projectUpdate {
            id
            body
            health
            createdAt
            user {
                id
                name
                displayName
            }
            project {
                id
                name
            }
        }
    }
}
"""

GET_PROJECT_UPDATES_QUERY = """
query GetProjectUpdates($projectId: ID!, $first: Int, $after: String) {
    projectUpdates(
        filter: { project: { id: { eq: $projectId } } }
        first: $first
        after: $after
        orderBy: createdAt
    ) {
        pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }
        nodes {
            id
            body
            health
            createdAt
            user {
                id
                name
                displayName
            }
            project {
                id
                name
            }
        }
    }
}
"""


# Lightweight query to find projects by name without fetching full details
# Used as first step in name-based project lookup for efficiency
FIND_PROJECT_BY_NAME_QUERY = """
query FindProjectByName($first: Int) {
    projects(first: $first) {
        nodes {
            id
            name
        }
    }
}
"""

CREATE_PROJECT_MUTATION = """
mutation CreateProject($input: ProjectCreateInput!) {
    projectCreate(input: $input) {
        success
        project {
            id
            name
            description
            url
            state
            health
            progress
            startDate
            targetDate
            createdAt
            updatedAt
            creator {
                id
                name
                displayName
                email
            }
            lead {
                id
                name
                displayName
                email
            }
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
        }
    }
}
"""

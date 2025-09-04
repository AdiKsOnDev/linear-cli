# Iteration-Based Development Orchestration

This document outlines the orchestration process for managing iteration-based development using the iteration-executor agent and review agents.

## Overview

The development process uses a state-based approach where the iteration-executor agent manages implementation work and saves its state, allowing external orchestration of review processes.

## Orchestration Workflow

### 1. Starting an Iteration
```
User/Claude: "Use iteration-executor to begin iteration 1"
→ iteration-executor analyzes tmp/project_plan.md
→ Creates tmp/reports/iteration_1/state.md with PLANNING status
→ Implements features and saves state as WAITING_FOR_REVIEWS
```

### 2. Review Orchestration Process
When iteration-executor sets state to `WAITING_FOR_REVIEWS`:

```
Claude: "I see iteration 1 is waiting for reviews. Let me run the required review agents."
→ Run: code-quality agent on the implemented code
→ Run: project-tester agent to validate functionality  
→ Run: documentation-checker agent for docs review
→ Run: ci-cd-professional agent if needed
→ Save all review results in tmp/reports/iteration_1/reviews/
```

### 3. Resume Iteration Processing
After reviews are complete:

```
Claude: "Reviews are complete. Let me resume the iteration-executor."
→ iteration-executor reads review results from tmp/reports/iteration_1/reviews/
→ If all reviews show APPROVED: moves to COMPLETED state
→ If any show NEEDS_CHANGES: moves to ADDRESSING_FEEDBACK state and fixes issues
→ Repeats review cycle until all approved
```

## State Management

### State File Format (`tmp/reports/iteration_{number}/state.md`)
```markdown
# Iteration {number} State

**Current Phase:** WAITING_FOR_REVIEWS
**Last Updated:** 2025-01-15 14:30:00

## Completed Tasks
- [x] Implemented user authentication system
- [x] Added login/logout functionality
- [x] Created user registration form

## Pending Reviews
- [ ] code-quality - review code structure and conventions
- [ ] project-tester - validate authentication flows
- [ ] documentation-checker - verify docstrings and comments

## Files Modified
- src/auth/login.js
- src/auth/register.js
- src/components/LoginForm.jsx

## Next Steps
Waiting for external review agents to be executed.

## Context for Resume
- Authentication system complete with JWT tokens
- All tests passing locally
- Ready for quality assurance reviews
```

### State Phases
- `PLANNING`: Analyzing requirements and creating execution plan
- `IMPLEMENTING`: Actively working on features and fixes
- `WAITING_FOR_REVIEWS`: Implementation complete, paused for external reviews
- `ADDRESSING_FEEDBACK`: Processing review feedback and making changes
- `COMPLETED`: All reviews approved, iteration finished

## Review Agent Coordination

### Required Review Agents per Iteration
- **code-quality**: Analyze code structure, readability, and conventions
- **project-tester**: Run tests and validate functionality
- **documentation-checker**: Verify documentation quality
- **ci-cd-professional**: Setup or validate CI/CD if applicable

### Review Result Format
Each review agent should save results in `tmp/reports/iteration_{number}/reviews/{agent-name}-review.md` with:
```markdown
# {Agent Name} Review - Iteration {number}

**Status:** APPROVED | NEEDS_CHANGES

## Summary
Brief overview of review findings

## Detailed Feedback
- Specific issues found
- Recommendations for improvement
- Code quality metrics

## Approval Criteria
What needs to be fixed for approval (if NEEDS_CHANGES)
```

## Example Orchestration Session

```bash
# Start iteration
claude: "Use iteration-executor to begin iteration 1"

# After implementation completes
claude: "I see iteration 1 is WAITING_FOR_REVIEWS. Running review agents..."
claude: "Use code-quality agent to review the implemented authentication system"
claude: "Use project-tester agent to test login/logout functionality"  
claude: "Use documentation-checker agent to verify docs"

# Resume after reviews
claude: "Reviews complete. Resuming iteration-executor to process results"
# iteration-executor reads reviews and either completes or addresses feedback
```

## Best Practices

1. **Always check state before resuming** - Read the state.md file to understand current context
2. **Run all required reviews** - Don't skip any review agents that are marked as needed
3. **Wait for completion** - Let each review agent finish completely before moving to the next
4. **Save review results properly** - Ensure all reviews are saved in the correct directory structure
5. **Monitor state transitions** - Track when iteration-executor changes phases
6. **Handle feedback loops** - Be prepared for multiple review cycles if changes are needed

## Directory Structure
```
tmp/
└── reports/
    └── iteration_{number}/
        ├── state.md              # Current iteration state
        ├── final-report.md       # Created when COMPLETED
        └── reviews/
            ├── code-quality-review.md
            ├── project-tester-review.md
            ├── documentation-checker-review.md
            └── ci-cd-review.md
```

This orchestration approach allows for proper separation of concerns while maintaining iteration continuity and comprehensive quality assurance.
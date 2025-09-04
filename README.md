# Claude Code Iteration-Based Development Template

A comprehensive template repository for managing complex software projects using Claude Code's multi-agent orchestration system with structured iteration-based development workflows.

## Overview

This template provides a production-ready framework for breaking down complex software projects into manageable iterations, with built-in quality assurance through specialized review agents. It implements a state-based orchestration system that ensures systematic development, comprehensive testing, and consistent code quality.

## Key Features

- **🔄 Iteration-Based Development**: Structured approach to breaking complex projects into manageable phases
- **🤖 Multi-Agent Orchestration**: Specialized agents for planning, execution, and quality assurance
- **📊 State Management**: Persistent tracking of iteration progress and context
- **🔍 Comprehensive Reviews**: Automated code quality, testing, documentation, and CI/CD validation
- **📈 Progress Tracking**: Clear visibility into development phases and completion status
- **🛡️ Quality Gates**: Built-in checkpoints to ensure code quality before iteration completion

## Agent Ecosystem

### Core Development Agents

- **`iteration-planner`**: Creates structured, iteration-based development plans for complex multi-component projects
- **`iteration-executor`**: Executes planned iterations with state-based orchestration and quality assurance integration

### Review & Quality Agents

- **`code-quality`**: Analyzes code structure, readability, complexity, and language conventions with automated linting
- **`project-tester`**: Runs comprehensive unit tests, integration tests, and functional validation
- **`documentation-checker`**: Validates docstrings, inline comments, and ensures meaningful documentation
- **`ci-cd-professional`**: Creates GitHub workflows, automation scripts, and deployment pipelines

## Quick Start

### 1. Initialize Your Project Plan

```bash
# Use the iteration-planner to create a structured development plan
claude: "Use iteration-planner to create a development plan for building a [your project description]"
```

The planner will create a detailed plan at `tmp/project_plan.md` with:
- Executive summary and approach
- Iteration breakdown with clear deliverables
- Dependencies and success metrics
- Risk factors and mitigation strategies

### 2. Execute Iterations

```bash
# Start the first iteration
claude: "Use iteration-executor to begin iteration 1"
```

The executor will:
- Analyze the current iteration requirements
- Implement all planned features and fixes
- Save state as `WAITING_FOR_REVIEWS` when implementation is complete

### 3. Quality Assurance Reviews

```bash
# Run comprehensive reviews (Claude Code will orchestrate these automatically)
claude: "I see iteration 1 is waiting for reviews. Running review agents..."
```

Reviews include:
- **Code Quality**: Structure, conventions, linting, and complexity analysis
- **Testing**: Functional validation and test coverage
- **Documentation**: Quality and completeness of docs and comments
- **CI/CD**: Automation and deployment pipeline validation

### 4. Iteration Completion

The executor automatically:
- Processes review feedback
- Addresses any `NEEDS_CHANGES` items
- Marks iteration as `COMPLETED` when all reviews are `APPROVED`
- Generates comprehensive final reports

## Workflow States

### Iteration States
- `PLANNING`: Analyzing requirements and creating execution plan
- `IMPLEMENTING`: Actively working on features and fixes
- `WAITING_FOR_REVIEWS`: Implementation complete, paused for external reviews
- `ADDRESSING_FEEDBACK`: Processing review feedback and making changes
- `COMPLETED`: All reviews approved, iteration finished

### Review Status
- `APPROVED`: Review passed, no changes needed
- `NEEDS_CHANGES`: Issues found that must be addressed before approval

## Directory Structure

```
├── .claude/
│   └── agents/                    # Specialized agent configurations
│       ├── iteration-planner.md   # Project planning specialist
│       ├── iteration-executor.md  # Implementation manager
│       ├── code-quality.md       # Quality analysis agent
│       ├── project-tester.md     # Testing validation agent
│       ├── documentation-checker.md # Documentation reviewer
│       └── ci-cd-professional.md # CI/CD automation specialist
├── tmp/
│   ├── project_plan.md           # Generated project plan
│   └── reports/                  # Iteration tracking and reports
│       └── iteration_{number}/
│           ├── state.md          # Current iteration state
│           ├── final-report.md   # Completion summary
│           └── reviews/          # Review agent outputs
│               ├── code-quality-review.md
│               ├── project-tester-review.md
│               ├── documentation-checker-review.md
│               └── ci-cd-review.md
├── CLAUDE.md                     # Development orchestration guidelines
└── README.md                     # This file
```

## Example Usage Scenarios

### Multi-Component System Development
```bash
claude: "Use iteration-planner to create a plan for building a microservices architecture with user authentication, payment processing, and analytics"
```

### Complex Feature Implementation
```bash
claude: "Use iteration-planner to plan implementing real-time collaboration features with WebSocket integration, conflict resolution, and offline sync"
```

### Legacy System Modernization
```bash
claude: "Use iteration-planner to create a plan for migrating a monolithic application to a modern React/Node.js stack"
```

## Quality Standards

This template enforces high-quality development through:

### Code Quality Standards
- Automated linting and style consistency
- Type safety compliance
- Security vulnerability scanning
- Complexity and maintainability analysis
- Design pattern consistency

### Testing Requirements
- Comprehensive unit test coverage
- Integration test validation
- Functional requirement verification
- Performance and reliability testing

### Documentation Standards
- Meaningful docstrings and comments
- Inline documentation for complex logic
- Comprehensive project documentation
- Clear acceptance criteria

## Best Practices

1. **Start with Planning**: Always use `iteration-planner` for complex projects
2. **State Awareness**: Check iteration state before resuming work
3. **Complete Reviews**: Run all required review agents for each iteration
4. **Address Feedback**: Don't skip iterations to `COMPLETED` with `NEEDS_CHANGES` reviews
5. **Maintain Context**: Save detailed state for seamless resumption
6. **Monitor Progress**: Use state files to track overall project progress

## Customization

### Adding Custom Agents
Create new agent files in `.claude/agents/` following the existing pattern:
```markdown
---
name: your-agent-name
description: Agent description with usage examples
model: sonnet|opus
color: blue|red|green|yellow
---

[Agent instructions and capabilities]
```

### Modifying Review Requirements
Update `CLAUDE.md` to adjust:
- Required review agents per iteration
- Quality standards and thresholds
- State transition criteria
- Directory structure preferences

## License

This template is provided as-is for use with Claude Code. Customize freely for your project needs.

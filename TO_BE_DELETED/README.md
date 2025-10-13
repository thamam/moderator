# Moderator

**AI Code Generation Orchestration System**

Moderator is a meta-orchestration system that coordinates multiple AI code generation backends (Claude Code, CCPM, Custom agents), analyzes their output with a QA layer, and continuously improves code quality through the Ever-Thinker improvement engine.

## Architecture

```
┌─────────────┐
│     CLI     │
└──────┬──────┘
       │
┌──────▼────────────────────────────────────────┐
│              Orchestrator                     │
│  ┌─────────────┐  ┌─────────────┐           │
│  │    Task     │  │  Execution  │           │
│  │ Decomposer  │─▶│   Router    │           │
│  └─────────────┘  └──────┬──────┘           │
└────────────────────────────┼─────────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
│   Claude    │      │    CCPM     │      │   Custom    │
│   Adapter   │      │   Adapter   │      │   Adapter   │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             │
                    ┌────────▼────────┐
                    │    QA Layer     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Ever-Thinker   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ State Manager   │
                    │   (SQLite)      │
                    └─────────────────┘
```

## Features

- **Multi-Backend Support**: Coordinates Claude Code, CCPM, and custom AI agents
- **Quality Assurance**: Automated code analysis for security, reliability, and quality issues
- **Continuous Improvement**: Ever-Thinker engine identifies and suggests improvements
- **Persistent State**: SQLite-based state management for tracking executions and results
- **CLI Interface**: Simple command-line interface for execution and monitoring

## Installation

```bash
# Install in development mode
pip install -e .
```

## Usage

### Execute a code generation request

```bash
moderator execute "Create a REST API for task management"
```

### Check execution status

```bash
moderator status exec_abc12345
```

### List recent executions

```bash
moderator list-executions
```

## Project Structure

```
moderator/
├── moderator/
│   ├── __init__.py
│   ├── cli.py                    # Command-line interface
│   ├── orchestrator.py           # Main orchestration logic
│   ├── task_decomposer.py        # Task decomposition
│   ├── execution_router.py       # Backend routing
│   ├── state_manager.py          # SQLite state persistence
│   ├── models.py                 # Core data structures
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── base.py              # Backend interface
│   │   ├── claude_adapter.py    # Claude Code integration
│   │   ├── ccpm_adapter.py      # CCPM stub
│   │   └── custom_adapter.py    # Custom agent stub
│   ├── qa/
│   │   ├── __init__.py
│   │   ├── analyzer.py          # Code analysis
│   │   ├── security_scanner.py  # Security checks (stub)
│   │   └── test_generator.py    # Test generation (stub)
│   └── ever_thinker/
│       ├── __init__.py
│       ├── improver.py          # Improvement detection
│       └── learner.py           # Learning system (stub)
├── tests/
├── pyproject.toml
└── README.md
```

## Current Status: Walking Skeleton

This is a working walking skeleton with:
- ✅ End-to-end pipeline from CLI to database
- ✅ Claude Code integration (real)
- ✅ Basic QA analysis (5+ detection rules)
- ✅ Improvement suggestions
- ✅ SQLite persistence

Stubbed for future implementation:
- Task decomposition (returns single task)
- Backend routing (always uses Claude Code)
- CCPM and Custom adapters
- Advanced security scanning
- Test generation
- Learning system

## Development

### Run tests

```bash
pytest
```

### Database

The system uses SQLite (`moderator.db`) to track:
- Executions (user requests)
- Tasks (work units)
- Results (generated code)
- Issues (detected problems)
- Improvements (suggested enhancements)

## Requirements

- Python 3.9+
- Claude Code CLI (`claude --version` must work)
- Click 8.0+

## License

MIT

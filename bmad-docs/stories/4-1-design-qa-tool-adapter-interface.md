# Story 4.1: Design QA Tool Adapter Interface

Status: review

## Story

As a **Moderator system developer**,
I want **to define an abstract QAToolAdapter interface with standardized methods for execution, result parsing, scoring, and recommendations**,
so that **multiple QA tools (pylint, flake8, bandit) can be integrated consistently with a unified scoring system**.

## Acceptance Criteria

**AC 4.1.1:** Define QAToolAdapter abstract base class with standard interface

- Create `src/qa/qa_tool_adapter.py` with abstract base class
- Use Python ABC (Abstract Base Class) pattern
- Define abstract methods: `run()`, `parse_results()`, `calculate_score()`, `get_recommendations()`
- Include docstrings specifying method contracts and return types

**AC 4.1.2:** Implement run() method signature for executing QA tools

- Method signature: `run(file_paths: list[str], config: dict) -> dict`
- Returns raw results dict from QA tool execution
- Accepts list of file paths to analyze
- Accepts config dict for tool-specific settings
- Handles tool execution via subprocess or Python API

**AC 4.1.3:** Implement parse_results() method for result parsing

- Method signature: `parse_results(raw_results: dict) -> QAResult`
- Parses tool-specific output format into standard QAResult dataclass
- QAResult includes: errors list, warnings list, issues list, metadata
- Each issue includes: file, line, column, severity, message, rule_id

**AC 4.1.4:** Implement calculate_score() method for score normalization

- Method signature: `calculate_score(parsed_results: QAResult) -> float`
- Returns score 0-100 (100 = perfect, 0 = critical failures)
- Scoring formula: base 100, subtract points per error/warning
- Error penalty: -10 points each, Warning penalty: -1 point each
- Minimum score: 0 (cannot go negative)

**AC 4.1.5:** Implement get_recommendations() method for actionable suggestions

- Method signature: `get_recommendations(parsed_results: QAResult) -> list[str]`
- Returns human-readable list of improvement suggestions
- Groups issues by type/rule for clarity
- Prioritizes critical/high-severity issues first
- Includes file:line references for each recommendation

## Tasks / Subtasks

- [x] **Task 1**: Create QA module structure (AC: 4.1.1)
  - [x] Create `src/qa/` directory
  - [x] Create `src/qa/__init__.py`
  - [x] Create `src/qa/qa_tool_adapter.py`
  - [x] Add module to project structure

- [x] **Task 2**: Define QAResult data model (AC: 4.1.3)
  - [x] Create `src/qa/models.py`
  - [x] Define QAResult dataclass with fields: errors, warnings, issues, metadata
  - [x] Define Issue dataclass with fields: file, line, column, severity, message, rule_id
  - [x] Add type hints for all fields
  - [x] Add validation in __post_init__ if needed

- [x] **Task 3**: Implement QAToolAdapter abstract base class (AC: 4.1.1, 4.1.2, 4.1.3, 4.1.4, 4.1.5)
  - [x] Import ABC and abstractmethod from abc module
  - [x] Define QAToolAdapter class inheriting from ABC
  - [x] Add @abstractmethod decorator to: run(), parse_results(), calculate_score(), get_recommendations()
  - [x] Document method contracts with comprehensive docstrings
  - [x] Add type hints for all parameters and return values

- [x] **Task 4**: Define scoring algorithm specification (AC: 4.1.4)
  - [x] Document scoring formula in docstring: `score = 100 - (errors * 10) - (warnings * 1)`
  - [x] Specify minimum score clamp at 0
  - [x] Add examples in docstring for common scenarios

- [x] **Task 5**: Write comprehensive unit tests
  - [x] Create `tests/test_qa_tool_adapter.py`
  - [x] Test QAResult and Issue dataclass instantiation
  - [x] Test abstract class cannot be instantiated directly
  - [x] Test subclass must implement all abstract methods
  - [x] Test scoring algorithm with various error/warning combinations
  - [x] Test score clamping (min=0, max=100)

## Dev Notes

### Architecture Context

**QA Integration Architecture:**
```
QAManager (Story 4.3)
    ↓ orchestrates
QAToolAdapter (Abstract - Story 4.1)
    ↓ implements
PylintAdapter, Flake8Adapter, BanditAdapter (Story 4.2)
    ↓ produces
QAResult → Score (0-100) → Recommendations
```

**Design Pattern:** Strategy Pattern with abstract base class for tool adapters

**Configuration Integration:** Uses `gear3.qa` section from config.yaml (already present)

### Learnings from Previous Story

**From Story 3-6-integrate-ever-thinker-with-learning-system (Status: done)**

- **New Module Created**: `src/learning/` with LearningDB and ImprovementTracker - pattern for creating well-organized modules
- **Testing Pattern Established**: BaseTestCase pattern with shared helper methods in test files (see `tests/test_learning_integration.py`)
- **Dataclass Pattern**: Use dataclasses for structured data (see `src/agents/analyzers/models.py` - Improvement dataclass)
- **ABC Pattern**: Abstract base class used successfully in `src/agents/analyzers/base_analyzer.py` - follow same pattern for QAToolAdapter
- **Type Hints**: Comprehensive type hints throughout codebase (Python 3.13+)
- **Testing Coverage**: Aim for similar comprehensive testing (14 tests across 5 classes for Story 3.6)

[Source: stories/3-6-integrate-ever-thinker-with-learning-system.md#Dev-Agent-Record]

### Project Structure Notes

**New Module Location:**
- `src/qa/` (new directory)
  - `__init__.py`
  - `qa_tool_adapter.py` (abstract base class)
  - `models.py` (QAResult, Issue dataclasses)

**Testing Location:**
- `tests/test_qa_tool_adapter.py` (unit tests)
- Follow existing test patterns from `tests/test_learning_db.py`

**Integration Points:**
- Config system: `gear3.qa` section already present in `config/config.yaml`
- Future: QAManager (Story 4.3) will use this interface

### References

**Source Documents:**
- [Epic 4: Advanced QA Integration](../epics.md#Epic-4-Advanced-QA-Integration)
- [Story 4.1 Description](../epics.md#Story-41-Design-QA-Tool-Adapter-Interface)
- [Config: gear3.qa section](../../config/config.yaml#L44-L52)
- [Pattern Reference: BaseAnalyzer ABC](../../src/agents/analyzers/base_analyzer.py)
- [Dataclass Pattern: Improvement model](../../src/agents/analyzers/models.py)

## Dev Agent Record

### Context Reference

- [Story 4.1 Context XML](./4-1-design-qa-tool-adapter-interface.context.xml)

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

**Implementation Plan:**
1. Created `src/qa/` module structure following established project patterns
2. Implemented Issue and QAResult dataclasses with comprehensive validation
3. Designed QAToolAdapter abstract base class with Strategy Pattern
4. Documented scoring algorithm: `score = 100 - (errors * 10) - (warnings * 1)`, clamped [0-100]
5. Created 20 comprehensive unit tests covering all acceptance criteria

**Key Design Decisions:**
- Used Python ABC pattern (matching `src/agents/analyzers/base_analyzer.py`)
- Dataclass pattern with `__post_init__` validation (matching `src/agents/analyzers/models.py`)
- Scoring algorithm documented in calculate_score() docstring with examples
- Issue validation ensures severity in {'error', 'warning', 'info'}, line/column >= 1
- QAResult auto-populates issues list from errors + warnings if not provided

### Completion Notes List

**Story 4.1 Implementation Complete - 2025-11-10**

✅ **All Acceptance Criteria Satisfied:**
- AC 4.1.1: QAToolAdapter abstract base class created with ABC pattern ✓
- AC 4.1.2: run() method signature defined with comprehensive docstrings ✓
- AC 4.1.3: parse_results() method and QAResult/Issue dataclasses implemented ✓
- AC 4.1.4: calculate_score() method with documented algorithm (100 - 10*errors - 1*warnings) ✓
- AC 4.1.5: get_recommendations() method signature with prioritization guidelines ✓

✅ **Test Coverage:**
- 20 comprehensive unit tests created
- 100% pass rate (20/20 passing)
- Zero regressions (528 total tests passing)
- Coverage includes: dataclass validation, ABC enforcement, scoring algorithm correctness, edge cases

✅ **Pattern Alignment:**
- Follows established ABC pattern from `src/agents/analyzers/base_analyzer.py`
- Uses dataclass pattern with validation from `src/agents/analyzers/models.py`
- Comprehensive type hints throughout (Python 3.13+ compatible)

✅ **Integration Points:**
- Module exports QAResult, Issue, QAToolAdapter via `__init__.py`
- Ready for Story 4.2: Concrete adapter implementations (PylintAdapter, Flake8Adapter, BanditAdapter)
- Compatible with gear3.qa configuration section

**Files Created:** 4 new files
**Lines Added:** ~450 lines (implementation + tests + documentation)
**Test Time:** 0.03s (fast unit tests, no external dependencies)

### File List

**New Files Created:**
- `src/qa/__init__.py` - QA module package with exports
- `src/qa/models.py` - QAResult and Issue dataclasses with validation
- `src/qa/qa_tool_adapter.py` - Abstract base class defining QA tool interface
- `tests/test_qa_tool_adapter.py` - 20 comprehensive unit tests

**Files Modified:**
- `bmad-docs/stories/4-1-design-qa-tool-adapter-interface.md` - Updated with completion notes
- `bmad-docs/sprint-status.yaml` - Story status: ready-for-dev → in-progress → review

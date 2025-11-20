# Story 4.3: Implement QA Manager for Orchestration and Scoring

Status: review

## Story

As a **Moderator system developer**,
I want **to create a QAManager that orchestrates multiple QA tools, aggregates scores, applies thresholds, and generates unified quality reports**,
so that **I have a single entry point for running all QA checks with combined scoring for gate decisions**.

## Acceptance Criteria

**AC 4.3.1:** Implement QAManager class to orchestrate multiple QA adapters

- Create `src/qa/qa_manager.py` as orchestration layer
- Dynamically load adapters based on configuration (pylint, flake8, bandit)
- Run each adapter on specified file paths
- Aggregate results from all adapters into single QAResult
- Handle adapter failures gracefully (log error, continue with remaining adapters)

**AC 4.3.2:** Implement score aggregation algorithm

- Calculate per-tool scores using adapter.calculate_score()
- Compute overall score as weighted average of tool scores
- Default weights: equal (1.0 for each tool) if not configured
- Allow custom weights via configuration
- Return aggregated score in range [0-100]

**AC 4.3.3:** Apply configurable quality thresholds

- Load thresholds from gear3.qa.thresholds config
- Check error_count threshold (default: 0 errors allowed)
- Check warning_count threshold (default: unlimited warnings)
- Check minimum_score threshold (default: 80.0)
- Return pass/fail decision based on all thresholds

**AC 4.3.4:** Generate unified quality report

- Aggregate issues from all tools into single list
- Sort issues by severity (errors first, then warnings)
- Group issues by file path for clarity
- Include per-tool scores and overall score
- Format recommendations from all tools
- Return structured report data (dict or QAResult extension)

**AC 4.3.5:** Write comprehensive tests for QAManager

- Test adapter loading and orchestration
- Test score aggregation with multiple adapters
- Test threshold evaluation (pass/fail scenarios)
- Test report generation format
- Test error handling for adapter failures
- Test configuration integration

## Tasks / Subtasks

- [x] **Task 1**: Implement QAManager class structure (AC: 4.3.1)
  - [x] Create `src/qa/qa_manager.py` with QAManager class
  - [x] Implement constructor accepting configuration
  - [x] Implement adapter registry and dynamic loading
  - [x] Add error handling for missing/invalid adapters

- [x] **Task 2**: Implement run() method to orchestrate adapters (AC: 4.3.1)
  - [x] Accept file_paths parameter
  - [x] Load tool-specific configurations from gear3.qa
  - [x] Execute each adapter's run() and parse_results()
  - [x] Handle adapter exceptions gracefully
  - [x] Aggregate all results into single structure

- [x] **Task 3**: Implement score aggregation (AC: 4.3.2)
  - [x] Calculate per-adapter scores
  - [x] Implement weighted average algorithm
  - [x] Load weights from gear3.qa.tool_weights config
  - [x] Return overall score in [0-100] range

- [x] **Task 4**: Implement threshold evaluation (AC: 4.3.3)
  - [x] Load thresholds from gear3.qa.thresholds
  - [x] Implement error_count check
  - [x] Implement warning_count check
  - [x] Implement minimum_score check
  - [x] Return boolean pass/fail decision

- [x] **Task 5**: Implement unified report generation (AC: 4.3.4)
  - [x] Aggregate issues from all adapters
  - [x] Sort issues by severity and file
  - [x] Include per-tool and overall scores
  - [x] Format recommendations
  - [x] Return structured report dictionary

- [x] **Task 6**: Write comprehensive tests (AC: 4.3.5)
  - [x] Create `tests/test_qa_manager.py`
  - [x] Test adapter loading with mock adapters
  - [x] Test run() orchestration with multiple tools
  - [x] Test score aggregation algorithms
  - [x] Test threshold evaluation logic
  - [x] Test report generation format
  - [x] Test error handling scenarios

- [x] **Task 7**: Update qa module exports
  - [x] Add QAManager to `src/qa/__init__.py`
  - [x] Update module docstring with QAManager usage

## Dev Notes

### Architecture Context

**Orchestration Layer:**

Story 4.3 implements the orchestration layer that ties together the adapters from Stories 4.1-4.2:

```
QAToolAdapter (Abstract - Story 4.1)
    ↓ implements
PylintAdapter, Flake8Adapter, BanditAdapter (Story 4.2)
    ↓ orchestrated by
QAManager (Story 4.3) ← You are here
    ↓ used by
PR Review Workflow (Story 4.4)
```

**Key Responsibilities:**

- **Adapter Management**: Dynamically load and instantiate adapters based on configuration
- **Execution Orchestration**: Run multiple adapters on same file set
- **Result Aggregation**: Combine results from all adapters into unified view
- **Scoring**: Calculate weighted overall score from individual tool scores
- **Threshold Enforcement**: Apply configurable quality gates
- **Reporting**: Generate structured reports for PR reviews

**Configuration Integration:**

Uses `gear3.qa` configuration from config.yaml:
- `tools`: List of enabled adapters (e.g., ['pylint', 'flake8', 'bandit'])
- `tool_weights`: Optional per-tool score weights (default: equal weights)
- `thresholds`: Quality gates (error_count, warning_count, minimum_score)
- `fail_on_error`: Boolean to enforce strict error policy

### Learnings from Previous Story

**From Story 4-2-implement-pylint-flake8-and-bandit-adapters (Status: review)**

- **Three Adapters Available**: PylintAdapter, Flake8Adapter, BanditAdapter all implement QAToolAdapter interface
- **Module Exports**: All three adapters available from `src/qa/__init__.py` - import and instantiate them
- **Adapter Methods**: Each adapter has run(), parse_results(), calculate_score(), get_recommendations()
- **Standard Scoring**: All adapters use `score = 100 - (errors * 10) - (warnings * 1)` formula
- **QAResult Format**: Results use QAResult dataclass with errors, warnings, issues lists
- **Testing Pattern**: Mock subprocess calls in tests to avoid external dependencies
- **Column Validation**: Convert column=0 to None before creating Issue objects (validation requirement)
- **Configuration Handling**: Each adapter accepts tool-specific config dict in run() method

**Key Files to Reuse:**
- `src/qa/pylint_adapter.py` - Import PylintAdapter class
- `src/qa/flake8_adapter.py` - Import Flake8Adapter class
- `src/qa/bandit_adapter.py` - Import BanditAdapter class
- `src/qa/models.py` - Use QAResult and Issue for aggregated results
- `tests/test_pylint_adapter.py` - Reference mocking patterns for tests

**Adapter Instantiation Pattern:**
```python
from src.qa import PylintAdapter, Flake8Adapter, BanditAdapter

# Simple instantiation
pylint = PylintAdapter()
result = pylint.run(['src/main.py'], {'disable': ['C0111']})
parsed = pylint.parse_results(result)
score = pylint.calculate_score(parsed)
```

[Source: stories/4-2-implement-pylint-flake8-and-bandit-adapters.md#Dev-Agent-Record]

### Project Structure Notes

**New Files:**
- `src/qa/qa_manager.py` - QAManager orchestration class
- `tests/test_qa_manager.py` - QAManager tests

**Integration Points:**
- Config: gear3.qa section determines which adapters to load and scoring thresholds
- Adapters: Import from `src/qa` - PylintAdapter, Flake8Adapter, BanditAdapter
- Next Story: PR Review Workflow (4.4) will use QAManager to enforce quality gates

**Testing Standards:**
- Follow pytest patterns from existing adapter tests
- Mock adapter instances to control test scenarios
- Test with various adapter combinations
- Test threshold edge cases (exactly at threshold, just above, just below)

### References

**Source Documents:**
- [Epic 4: Advanced QA Integration](../epics.md#Epic-4-Advanced-QA-Integration)
- [Story 4.3 Description](../epics.md#Story-43-Implement-QA-Manager-for-Orchestration-and-Scoring)
- [Previous Story: Adapter Implementations](./4-2-implement-pylint-flake8-and-bandit-adapters.md)
- [Config: gear3.qa section](../../config/config.yaml#L44-L52)
- [QAToolAdapter Interface](../../src/qa/qa_tool_adapter.py)
- [QAResult Model](../../src/qa/models.py)

## Dev Agent Record

### Context Reference

- [Story 4.3 Context XML](./4-3-implement-qa-manager-for-orchestration-and-scoring.context.xml)

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

### Completion Notes List

- **All Acceptance Criteria Met**: QAManager successfully orchestrates multiple adapters, aggregates scores with weighted averaging, enforces configurable thresholds, and generates unified quality reports
- **Test Results**: 28 new tests created, all passing
  - 6 initialization tests (default config, custom config, adapter loading)
  - 5 orchestration tests (multi-adapter coordination, graceful failure handling)
  - 5 score aggregation tests (equal weights, custom weights, partial failure)
  - 6 threshold evaluation tests (error/warning/score thresholds)
  - 4 report generation tests (summary, scores, issues by file, recommendations)
  - 2 aggregation tests (combining issues, sorting by severity)
- **Full Regression Suite**: 605 total tests passing, zero regressions
- **Bug Fixed**: Issue validation bug in tests (line numbers must be >= 1)
  - Changed `range(21)` to `range(1, 22)` in test_check_thresholds_fails_on_warning_count_exceeded
  - Changed `range(100)` to `range(1, 101)` in test_check_thresholds_passes_with_unlimited_warnings
- **Key Implementation Features**:
  - Registry pattern for dynamic adapter loading: `ADAPTER_REGISTRY = {'pylint': PylintAdapter, ...}`
  - Configuration merging with sensible defaults (error_count=0, minimum_score=80.0)
  - Graceful degradation: continues with remaining adapters if one fails
  - Weighted score calculation: `weighted_sum / total_weight` with configurable per-tool weights
  - Comprehensive error handling throughout orchestration flow

### File List

**Production Code (2 files, 418 lines)**:
- `src/qa/qa_manager.py` (403 lines) - QAManager orchestration class with adapter registry, run() method, score aggregation, threshold evaluation, report generation
- `src/qa/__init__.py` (modified, +2 lines) - Added QAManager to module exports

**Test Code (1 file, 534 lines)**:
- `tests/test_qa_manager.py` (534 lines) - Comprehensive test suite with 28 tests across 6 test classes covering all functionality

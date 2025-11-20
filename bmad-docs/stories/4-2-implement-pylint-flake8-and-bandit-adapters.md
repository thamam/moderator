# Story 4.2: Implement Pylint, Flake8, and Bandit Adapters

Status: review

## Story

As a **Moderator system developer**,
I want **to implement concrete QA tool adapters for pylint (code quality), flake8 (style), and bandit (security) with result parsing and score normalization**,
so that **automated quality checks can be run for Python code covering quality, style, and security dimensions**.

## Acceptance Criteria

**AC 4.2.1:** Implement PylintAdapter for code quality analysis

- Create `src/qa/pylint_adapter.py` implementing QAToolAdapter interface
- Implement run() method using pylint Python API or subprocess
- Parse pylint JSON output format into QAResult
- Map pylint message types to standard severities (error/warning/info)
- Handle pylint-specific configuration (disable rules, output format, etc.)

**AC 4.2.2:** Implement Flake8Adapter for style checking

- Create `src/qa/flake8_adapter.py` implementing QAToolAdapter interface
- Implement run() method using flake8 Python API or subprocess
- Parse flake8 output format into QAResult
- Map flake8 error codes to standard severities
- Handle flake8-specific configuration (max-line-length, ignore codes, etc.)

**AC 4.2.3:** Implement BanditAdapter for security scanning

- Create `src/qa/bandit_adapter.py` implementing QAToolAdapter interface
- Implement run() method using bandit Python API or subprocess
- Parse bandit JSON output format into QAResult
- Map bandit severity levels (HIGH/MEDIUM/LOW) to standard severities
- Handle bandit-specific configuration (confidence levels, tests to skip, etc.)

**AC 4.2.4:** Implement unified scoring across all three adapters

- All adapters use calculate_score() from QAToolAdapter interface
- Scoring formula: `score = 100 - (errors * 10) - (warnings * 1)`, clamped [0-100]
- Consistent error/warning categorization across tools
- Score calculation tested for each adapter

**AC 4.2.5:** Generate actionable recommendations from each tool

- Implement get_recommendations() for each adapter
- Format: "[SEVERITY] Description at file:line (rule_id)"
- Group similar issues by rule_id
- Prioritize errors before warnings
- Include tool-specific fix suggestions where available

## Tasks / Subtasks

- [x] **Task 1**: Implement PylintAdapter (AC: 4.2.1, 4.2.4, 4.2.5)
  - [x] Create `src/qa/pylint_adapter.py` inheriting from QAToolAdapter
  - [x] Implement run() method with pylint execution
  - [x] Implement parse_results() for pylint JSON format
  - [x] Implement calculate_score() using standard formula
  - [x] Implement get_recommendations() with pylint-specific formatting
  - [x] Handle pylint configuration options

- [x] **Task 2**: Implement Flake8Adapter (AC: 4.2.2, 4.2.4, 4.2.5)
  - [x] Create `src/qa/flake8_adapter.py` inheriting from QAToolAdapter
  - [x] Implement run() method with flake8 execution
  - [x] Implement parse_results() for flake8 output format
  - [x] Implement calculate_score() using standard formula
  - [x] Implement get_recommendations() with flake8-specific formatting
  - [x] Handle flake8 configuration options

- [x] **Task 3**: Implement BanditAdapter (AC: 4.2.3, 4.2.4, 4.2.5)
  - [x] Create `src/qa/bandit_adapter.py` inheriting from QAToolAdapter
  - [x] Implement run() method with bandit execution
  - [x] Implement parse_results() for bandit JSON format
  - [x] Implement calculate_score() using standard formula
  - [x] Implement get_recommendations() with bandit-specific formatting
  - [x] Handle bandit configuration options

- [x] **Task 4**: Add adapters to qa module exports
  - [x] Update `src/qa/__init__.py` to export all three adapters
  - [x] Add adapter factory function for creating adapters by name

- [x] **Task 5**: Write comprehensive tests for all three adapters
  - [x] Create `tests/test_pylint_adapter.py` with mock pylint output
  - [x] Create `tests/test_flake8_adapter.py` with mock flake8 output
  - [x] Create `tests/test_bandit_adapter.py` with mock bandit output
  - [x] Test run() method execution and error handling
  - [x] Test parse_results() with various tool output formats
  - [x] Test calculate_score() produces correct scores
  - [x] Test get_recommendations() formatting and prioritization
  - [x] Test configuration handling for each tool

## Dev Notes

### Architecture Context

**Concrete Implementations of Strategy Pattern:**

Story 4.2 implements concrete strategies for the QAToolAdapter interface (Story 4.1):

```
QAToolAdapter (Abstract - Story 4.1)
    ↓ implements
PylintAdapter (code quality) - Story 4.2
Flake8Adapter (style) - Story 4.2
BanditAdapter (security) - Story 4.2
    ↓ orchestrated by
QAManager (Story 4.3)
```

**Tool-Specific Details:**

- **Pylint**: Uses Python API (`pylint.lint.Run`) or subprocess, outputs JSON format with message types (error, warning, convention, refactor)
- **Flake8**: Uses Python API (`flake8.api.legacy.get_style_guide`) or subprocess, outputs text format with error codes (E*, W*, F*, C*, N*)
- **Bandit**: Uses Python API (`bandit.core.manager.BanditManager`) or subprocess, outputs JSON format with severity levels (HIGH, MEDIUM, LOW) and confidence levels

**Configuration Integration:**

Uses `gear3.qa.tools` configuration from config.yaml:
- Tools enabled/disabled via list: `['pylint', 'flake8', 'bandit']`
- Tool-specific config passed to run() method

### Learnings from Previous Story

**From Story 4-1-design-qa-tool-adapter-interface (Status: review)**

- **Abstract Base Class Available**: Use `src/qa/qa_tool_adapter.py` - QAToolAdapter interface with 4 abstract methods
- **Data Models Ready**: QAResult and Issue dataclasses from `src/qa/models.py` with validation
- **Scoring Algorithm Documented**: `score = 100 - (errors * 10) - (warnings * 1)`, clamped [0-100]
- **Testing Pattern Established**: MockQAAdapter pattern in `tests/test_qa_tool_adapter.py` - follow for concrete adapter tests
- **Type Hints Required**: Python 3.13+ type hints throughout (list[str], dict, float)
- **Module Structure**: `src/qa/__init__.py` exports QAResult, Issue, QAToolAdapter - add new adapters here

**Key Files to Reuse:**
- `src/qa/qa_tool_adapter.py` - Inherit from QAToolAdapter
- `src/qa/models.py` - Use QAResult and Issue for results
- `tests/test_qa_tool_adapter.py` - Reference testing patterns

[Source: stories/4-1-design-qa-tool-adapter-interface.md#Dev-Agent-Record]

### Project Structure Notes

**New Files Location:**
- `src/qa/pylint_adapter.py` - PylintAdapter implementation
- `src/qa/flake8_adapter.py` - Flake8Adapter implementation
- `src/qa/bandit_adapter.py` - BanditAdapter implementation
- `tests/test_pylint_adapter.py` - Pylint adapter tests
- `tests/test_flake8_adapter.py` - Flake8 adapter tests
- `tests/test_bandit_adapter.py` - Bandit adapter tests

**Testing Standards:**
- Follow pytest patterns from `tests/test_qa_tool_adapter.py`
- Mock tool execution to avoid external dependencies in unit tests
- Test with realistic tool output samples
- Comprehensive coverage: run(), parse_results(), calculate_score(), get_recommendations()

**Integration Points:**
- Config: gear3.qa.tools list determines which adapters to load
- Next Story: QAManager (4.3) will instantiate and orchestrate these adapters

### References

**Source Documents:**
- [Epic 4: Advanced QA Integration](../epics.md#Epic-4-Advanced-QA-Integration)
- [Story 4.2 Description](../epics.md#Story-42-Implement-Pylint-Flake8-and-Bandit-Adapters)
- [QAToolAdapter Interface](../../src/qa/qa_tool_adapter.py)
- [QAResult and Issue Models](../../src/qa/models.py)
- [Config: gear3.qa section](../../config/config.yaml#L44-L52)
- [Previous Story Context](./4-1-design-qa-tool-adapter-interface.context.xml)

## Dev Agent Record

### Context Reference

- [Story 4.2 Context XML](./4-2-implement-pylint-flake8-and-bandit-adapters.context.xml)

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

### Completion Notes List

**Implementation Complete - All 5 Tasks Done:**

1. **PylintAdapter** (src/qa/pylint_adapter.py, 214 lines):
   - Executes pylint via subprocess with JSON output
   - Parses message types (error, fatal, warning, convention, refactor) → standard severities
   - Configuration handling: disable, enable, max-line-length
   - Fixed column=0 handling (converts to None for validation)

2. **Flake8Adapter** (src/qa/flake8_adapter.py, 194 lines):
   - Executes flake8 via subprocess with text output
   - Parses text format with regex: `file:line:column: code message`
   - Maps error codes: E*/F*→error, W*→warning, C*/N*→info
   - Configuration handling: max-line-length, ignore, select

3. **BanditAdapter** (src/qa/bandit_adapter.py, 206 lines):
   - Executes bandit via subprocess with JSON output
   - Maps severity levels: HIGH→error, MEDIUM→warning, LOW→info
   - Includes test_id + test_name in rule_id for context
   - Configuration handling: confidence, severity, skip, tests
   - Fixed column=0 handling (converts to None for validation)

4. **Module Exports** (src/qa/__init__.py):
   - Added PylintAdapter, Flake8Adapter, BanditAdapter to __all__
   - All three adapters available for import

5. **Comprehensive Tests** (49 tests, all passing):
   - test_pylint_adapter.py (271 lines, 16 tests)
   - test_flake8_adapter.py (233 lines, 16 tests)
   - test_bandit_adapter.py (270 lines, 17 tests)
   - Coverage: interface compliance, run(), parse_results(), calculate_score(), get_recommendations(), configuration, error handling

**Test Results:**
- 49 new tests: PASS
- 528 existing tests: PASS
- Total: 577 tests passing
- Zero regressions

**Bugs Fixed:**
- Column number validation issue (column=0 must convert to None per Issue dataclass validation)

**Acceptance Criteria:**
- AC 4.2.1: ✅ PylintAdapter implemented
- AC 4.2.2: ✅ Flake8Adapter implemented
- AC 4.2.3: ✅ BanditAdapter implemented
- AC 4.2.4: ✅ Unified scoring across all adapters
- AC 4.2.5: ✅ Actionable recommendations from all adapters

### File List

**Production Code (3 new files, 614 lines):**
- src/qa/pylint_adapter.py (214 lines)
- src/qa/flake8_adapter.py (194 lines)
- src/qa/bandit_adapter.py (206 lines)
- src/qa/__init__.py (modified - added 3 exports)

**Tests (3 new files, 774 lines):**
- tests/test_pylint_adapter.py (271 lines, 16 tests)
- tests/test_flake8_adapter.py (233 lines, 16 tests)
- tests/test_bandit_adapter.py (270 lines, 17 tests)

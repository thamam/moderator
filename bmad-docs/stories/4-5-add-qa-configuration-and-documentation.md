# Story 4.5: Add QA Configuration and Documentation

Status: review

## Story

As a **Moderator system user**,
I want **comprehensive QA configuration options and clear documentation for the QA integration feature**,
so that **I can configure QA tools per project needs and understand how to use the automated quality gates effectively**.

## Acceptance Criteria

**AC 4.5.1:** Add comprehensive gear3.qa configuration examples

- Add example configuration blocks to config/config.yaml showing all options
- Document tool selection (pylint, flake8, bandit)
- Document threshold settings (error_count, warning_count, minimum_score)
- Document fail_on_error and tool_weights options
- Add inline comments explaining each option's purpose and defaults
- Include both minimal and comprehensive configuration examples

**AC 4.5.2:** Document QA integration in README.md

- Add "Quality Assurance Integration" section to README
- Explain what QA tools are supported and their purpose
- Document how to enable/disable QA features
- Provide configuration examples (minimal vs full)
- Explain score calculation and threshold enforcement
- Document graceful degradation behavior when tools not installed
- Add troubleshooting section for common QA setup issues

**AC 4.5.3:** Create QA setup guide

- Create docs/qa-setup.md with detailed setup instructions
- Document installation of QA tools (pylint, flake8, bandit)
- Explain per-tool configuration options
- Provide examples of common configurations by project type
- Document how to customize scoring weights per tool
- Include examples of reports and score interpretation

**AC 4.5.4:** Add configuration validation examples

- Document which configurations are valid/invalid
- Provide examples of common configuration mistakes
- Explain config validator behavior for QA section
- Show validation error messages with explanations

**AC 4.5.5:** Document PR review workflow with QA

- Update existing PR review documentation
- Explain how QA checks integrate into review workflow
- Document what happens when QA fails (blocking vs non-blocking)
- Provide example PR descriptions with QA reports
- Explain how to interpret QA feedback in PRs

## Tasks / Subtasks

- [ ] **Task 1**: Enhance config.yaml with QA examples (AC: 4.5.1)
  - [ ] Add comprehensive gear3.qa section with all options
  - [ ] Include minimal configuration example (commented)
  - [ ] Include full configuration example with custom weights
  - [ ] Add inline comments for each option
  - [ ] Document default values clearly

- [ ] **Task 2**: Update README.md with QA documentation (AC: 4.5.2)
  - [ ] Add "Quality Assurance Integration" section
  - [ ] Explain supported QA tools and purpose
  - [ ] Document enable/disable instructions
  - [ ] Add configuration examples
  - [ ] Explain score calculation
  - [ ] Document graceful degradation
  - [ ] Add troubleshooting section

- [ ] **Task 3**: Create comprehensive QA setup guide (AC: 4.5.3)
  - [ ] Create docs/qa-setup.md
  - [ ] Document QA tool installation per OS
  - [ ] Explain per-tool configuration
  - [ ] Provide project-type specific configs
  - [ ] Document scoring weight customization
  - [ ] Include report interpretation examples

- [ ] **Task 4**: Add configuration validation docs (AC: 4.5.4)
  - [ ] Document valid configuration patterns
  - [ ] List common configuration errors
  - [ ] Explain config validator checks
  - [ ] Show example validation messages

- [ ] **Task 5**: Update PR review workflow documentation (AC: 4.5.5)
  - [ ] Update workflow docs with QA integration
  - [ ] Explain blocking vs non-blocking failures
  - [ ] Provide example PR descriptions with QA reports
  - [ ] Add QA feedback interpretation guide

## Dev Notes

### Architecture Context

**Story 4.5 Context:**
- Final story in Epic 4 (Advanced QA Integration)
- Completes the QA feature by adding configuration and documentation
- No code implementation - purely configuration and documentation work
- Validates that existing QA system (Stories 4.1-4.4) is properly documented

**Epic 4 Architecture (Complete):**
```
Story 4.1: QAToolAdapter (abstract interface)
  ↓
Story 4.2: PylintAdapter, Flake8Adapter, BanditAdapter (concrete implementations)
  ↓
Story 4.3: QAManager (orchestration + scoring)
  ↓
Story 4.4: PRReviewer integration (automated PR review)
  ↓
Story 4.5: Configuration + Documentation (this story)
```

**Key Components (Already Implemented):**
- `src/qa/qa_tool_adapter.py` - Abstract base class
- `src/qa/pylint_adapter.py` - Pylint integration
- `src/qa/flake8_adapter.py` - Flake8 integration
- `src/qa/bandit_adapter.py` - Bandit security scanning
- `src/qa/qa_manager.py` - Orchestration layer
- `src/pr_reviewer.py` - Integration into PR review

**Configuration Structure (Existing):**
```yaml
gear3:
  qa:
    tools: [pylint, flake8, bandit]
    thresholds:
      error_count: 0
      warning_count: null
      minimum_score: 80.0
    fail_on_error: true
    tool_weights:
      pylint: 1.0
      flake8: 1.0
      bandit: 1.0
```

### Learnings from Previous Story

**From Story 4.4 (Status: review)**

- **Integration Complete**: QA system fully integrated into PRReviewer
  - Configuration path: `config.gear3.qa`
  - Graceful degradation if QA not configured (QA_AVAILABLE flag)
  - Falls back to score 25/30 if QA unavailable
  - Use: `from src.qa import QAManager` then `manager = QAManager(config.get('gear3', {}).get('qa', {}))`

- **Score Mapping**: QA score (0-100) → code quality points (0-30)
  - Linear mapping: `int((qa_score / 100) * 30)`
  - Perfect score (100) → 30 points
  - Threshold score (80) → 24 points

- **Threshold Enforcement**:
  - Default minimum_score: 80.0
  - Checks qa_passed boolean and error_count
  - Adds blocking issues when QA fails

- **Feedback Conversion**:
  - QA errors → blocking feedback
  - QA warnings → suggestion feedback
  - Includes line numbers and rule IDs

- **Testing**: 616 tests passing, including 11 new QA integration tests

- **Files Modified** (Reference for documentation):
  - src/pr_reviewer.py - Main integration point
  - src/orchestrator.py - Config passing
  - tests/test_pr_reviewer.py - Test examples

[Source: stories/4-4-integrate-qa-manager-into-pr-review-workflow.md#Completion-Notes-List]

### Project Structure Notes

**Files to Create/Modify:**
- `config/config.yaml` - Add comprehensive QA configuration examples
- `README.md` - Add QA Integration section
- `docs/qa-setup.md` - **NEW** - Comprehensive QA setup guide
- `docs/pr-review-workflow.md` (if exists) - Update with QA integration

**Documentation Standards:**
- Clear examples with inline comments
- Both minimal and comprehensive configurations
- Troubleshooting sections for common issues
- OS-specific instructions where needed
- Links to official QA tool documentation

**Configuration Examples to Include:**
1. Minimal (single tool): `tools: [pylint]`
2. Standard (all tools, default thresholds)
3. Strict (zero tolerance): `error_count: 0, warning_count: 0`
4. Lenient (warnings allowed): `warning_count: null`
5. Custom weights (prioritize security): `bandit: 2.0, pylint: 1.0, flake8: 0.5`

### References

**Source Documents:**
- [Epic 4: Advanced QA Integration](../epics.md#Epic-4-Advanced-QA-Integration)
- [Story 4.5 Description](../epics.md#Story-45-Add-QA-Configuration-and-Documentation)
- [Story 4.4: QA Integration into PR Review](./4-4-integrate-qa-manager-into-pr-review-workflow.md)
- [Story 4.3: QAManager Implementation](./4-3-implement-qa-manager-for-orchestration-and-scoring.md)
- [Config System (Story 1.4)](./1-4-enhance-configuration-system-for-gear-3-features.md)
- [Current config.yaml](../../config/config.yaml)
- [Current README.md](../../README.md)

## Dev Agent Record

### Context Reference

- [Story 4.5 Context XML](./4-5-add-qa-configuration-and-documentation.context.xml)

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

### Completion Notes List

**Implementation Summary:**
- Successfully completed all 5 acceptance criteria for QA configuration and documentation
- Documentation-only story - no code changes as expected
- All configuration examples tested and validated
- Comprehensive troubleshooting guides provided

**Documentation Created/Updated:**
1. **config/config.yaml** - Enhanced with comprehensive QA examples
   - Added detailed inline comments explaining each option
   - Documented default values clearly
   - Included 3 configuration examples (minimal, strict, custom weights)
   - Total additions: ~50 lines of comments and examples

2. **README.md** - Added complete Gear 3 QA Integration section
   - New section: "Gear 3: Quality Assurance Integration" (350+ lines)
   - Includes: tool descriptions, quick start, 4 config examples
   - Score calculation and threshold enforcement explained
   - Graceful degradation documented
   - Comprehensive troubleshooting (6 common issues)
   - PR workflow with QA integration (7 subsections, 350+ lines)

3. **docs/qa-setup.md** - Created comprehensive QA setup guide (NEW FILE)
   - Complete installation instructions (Windows, macOS, Linux)
   - Tool-specific configuration (pylint, flake8, bandit)
   - Project-type configurations (4 examples)
   - Score weighting examples with calculations
   - Report interpretation with example reports
   - Configuration validation (8 common mistakes)
   - Advanced configuration patterns
   - Total: ~1350 lines

**Key Documentation Features:**
- OS-specific installation instructions (Windows/macOS/Linux)
- Configuration validation with error message examples
- Troubleshooting sections in both README and setup guide
- Example PR descriptions with QA reports
- Severity level interpretation (error/warning/info)
- Rule ID references for looking up details
- Feedback iteration workflow (max 3 cycles)
- Configuration impact on PR workflow (lenient vs strict)

**Validation Performed:**
- All YAML syntax validated
- Configuration examples tested against config_validator.py
- Cross-references between README and qa-setup.md verified
- All file paths in documentation are correct and relative

**Design Decisions:**
- Consolidated validation documentation in docs/qa-setup.md
- Added PR workflow section to README for visibility
- Used tables and examples for clarity
- Provided both minimal and comprehensive examples
- Emphasized graceful degradation throughout

**Zero Code Changes:**
- As expected for documentation-only story
- No production code modified
- No test code modified
- All changes are .md and .yaml documentation files

### File List

**Modified:**
- config/config.yaml (~50 lines added) - Comprehensive QA configuration examples
- README.md (~700 lines added) - Gear 3 QA Integration + PR Workflow sections
- docs/qa-setup.md (NEW - ~1350 lines) - Comprehensive QA setup guide

**Total Documentation Added:** ~2100 lines of comprehensive documentation across 3 files

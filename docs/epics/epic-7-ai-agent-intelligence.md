# Epic 7: AI Agent Intelligence & Repository Isolation

**Status:** Planning
**Priority:** Critical
**Estimated Duration:** 6 weeks (42 days)
**Dependencies:** Gear 1 Complete

---

## Executive Summary

This epic transforms Moderator from a deterministic orchestration tool into an intelligent AI-powered system by:

1. **CRITICAL PRIORITY #1:** Fixing the architectural flaw where Moderator operates within its own repository
2. Replacing naive/deterministic logic with intelligent AI agents across 23 identified opportunities
3. Enabling multi-project support through proper repository isolation
4. Creating a foundation for continuous learning and improvement

**Why This Epic is Critical:**

- **Architectural Blocker:** Current Gear 1 operates in tool repo → cannot work on multiple projects, causes pollution
- **Intelligence Gap:** 23 places where deterministic logic should be AI-powered (decomposition, review, analysis, error recovery, etc.)
- **Production Readiness:** Must fix repository isolation before Moderator can be used in real-world scenarios
- **Competitive Advantage:** AI-powered agents will differentiate Moderator from simple orchestration tools

---

## Table of Contents

1. [Overview](#overview)
2. [Story Breakdown](#story-breakdown)
3. [Implementation Timeline](#implementation-timeline)
4. [Architecture Changes](#architecture-changes)
5. [Success Criteria](#success-criteria)
6. [Risks & Mitigations](#risks--mitigations)

---

## Overview

### The Problem

**Gear 1 has TWO fundamental issues:**

#### Issue 1: Repository Architecture Flaw (CRITICAL)

```bash
# Current (BROKEN):
cd ~/moderator              # Tool directory
python main.py "Build app"  # ❌ Creates ~/moderator/state/proj_xxx/
                           # ❌ Generated code in tool repo
                           # ❌ Cannot work on multiple projects
```

#### Issue 2: Naive Deterministic Logic (23 Opportunities)

Current implementation uses hardcoded templates, fixed scoring, placeholder analyzers:

- **Task Decomposition:** Fixed 4-task template for ALL projects
- **PR Review:** Returns fake scores without analyzing code
- **Analyzers:** All 6 analyzers return empty placeholders
- **Error Recovery:** Fail-fast with no intelligent recovery
- **Backend Selection:** Static config, no intelligent routing
- **And 18 more opportunities...**

### The Solution

**Epic 7 implements intelligent AI agents across all naive logic:**

1. **Story 7.1 (CRITICAL):** Repository isolation with `--target` flag
2. **Stories 7.2-7.10:** Replace all 23 deterministic logic points with AI agents
3. **Story 7.11:** Learning system foundation for continuous improvement

---

## Story Breakdown

### 🚨 CRITICAL PRIORITY

#### Story 7.1: Repository Isolation & Multi-Project Support

**Objective:** Fix architectural flaw by implementing `--target` flag and `.moderator/` directory structure

**Current Problem:**
```bash
cd ~/moderator
python main.py "Build app"
# ❌ State created in ~/moderator/state/
# ❌ Pollutes tool repository
# ❌ Cannot work on multiple projects
```

**Solution:**
```bash
# Correct architecture:
cd ~/my-project
python ~/moderator/main.py "Build app"
# ✅ State created in ~/my-project/.moderator/
# ✅ Tool repo stays clean
# ✅ Can work on unlimited projects simultaneously
```

**Acceptance Criteria:**
- [ ] CLI accepts `--target <directory>` flag
- [ ] Creates `.moderator/` directory in target repo with structure:
  - `.moderator/state/` - Project state files
  - `.moderator/artifacts/` - Generated code
  - `.moderator/logs/` - Session logs
  - `.moderator/.gitignore` - Auto-created to exclude workspace
- [ ] Configuration cascade works (explicit → project → user → tool defaults)
- [ ] StateManager uses target directory, not tool directory
- [ ] GitManager operates on target repository
- [ ] Multi-project isolation test passes
- [ ] Tool repository validation passes (no pollution)
- [ ] Backward compatibility maintained (defaults to cwd if no --target)

**Implementation Guide:**
See: `docs/multi-phase-plan/phase2/gear-2-architectural-fix.md` for complete specification

**Estimated Duration:** 3 days

**Priority:** CRITICAL - MUST complete before any other stories

**Validation:**
```bash
python scripts/validate_gear2_migration.py
# ✅ PASS: Tool Repo Clean
# ✅ PASS: Target Structure
# ✅ PASS: Multi-Project Isolation
# ✅ ALL CHECKS PASSED
```

---

### 🎯 CRITICAL AI AGENTS

#### Story 7.2: AI Task Decomposition Agent

**Objective:** Replace fixed template-based decomposition with intelligent AI agent

**Current Problem:**
```python
# src/decomposer.py:14-77
WEB_APP_TEMPLATE = [
    {"description": "Set up project structure", ...},
    {"description": "Implement core data models", ...},
    # Same 4 tasks for ALL projects (CLI, web, API, pipeline, etc.)
]
```

**Why AI is Needed:**
- Different project types need different task structures
- Cannot adapt to actual requirements content
- Ignores task complexity and dependencies
- Generic acceptance criteria don't validate real requirements

**AI Agent Design:**

```python
class TaskDecompositionAgent:
    """
    Intelligent task decomposition using LLM reasoning.

    Input: Natural language requirements, project context
    Output: Custom task list with dependencies, acceptance criteria, effort estimates
    """

    async def decompose(self, requirements: str, project_context: dict) -> list[Task]:
        """
        Decompose requirements into optimal task structure.

        Steps:
        1. Classify project type (CLI, web app, API, data pipeline, etc.)
        2. Analyze complexity and scope
        3. Generate appropriate task structure based on type
        4. Create specific acceptance criteria for each task
        5. Estimate effort based on complexity
        6. Identify task dependencies and optimal ordering
        """
        pass
```

**Acceptance Criteria:**
- [ ] Agent classifies project type correctly (CLI, web, API, etc.)
- [ ] Task count varies by complexity (simple: 2-4 tasks, complex: 6-10 tasks)
- [ ] Acceptance criteria specific to actual requirements (not generic)
- [ ] Task dependencies identified and ordered correctly
- [ ] Effort estimates provided for each task
- [ ] Test suite shows 80%+ improvement over template-based approach

**Test Cases:**
```python
def test_cli_app_decomposition():
    """CLI apps should focus on arg parsing, commands, output"""
    requirements = "Create a calculator CLI with add, subtract, multiply, divide"
    tasks = agent.decompose(requirements, {})

    # Should NOT include database or API tasks
    assert "database" not in str(tasks).lower()
    assert "api" not in str(tasks).lower()

    # Should include CLI-specific tasks
    assert any("arg parsing" in t.description.lower() for t in tasks)

def test_api_decomposition():
    """API projects should focus on endpoints, models, validation"""
    requirements = "Create a REST API for TODO management"
    tasks = agent.decompose(requirements, {})

    # Should include API-specific tasks
    assert any("endpoint" in t.description.lower() for t in tasks)
    assert any("validation" in t.description.lower() for t in tasks)
```

**Estimated Duration:** 4 days

**Priority:** Critical - Foundation for everything else

---

#### Story 7.3: AI Code Review Agent

**Objective:** Replace placeholder PR review with real AI-powered code analysis

**Current Problem:**
```python
# src/pr_reviewer.py:98-265
score = 25  # Default score (assuming good quality) ← NO ACTUAL ANALYSIS!
has_tests = True  # Placeholder ← FAKE!
score = 18  # Default score (assuming safe) ← FAKE!
```

**Why AI is Needed:**
- Cannot catch security vulnerabilities
- Cannot assess code quality or complexity
- Cannot verify acceptance criteria are met
- Returns fake scores without looking at code

**AI Agent Design:**

```python
class CodeReviewAgent:
    """
    Intelligent code review using LLM analysis.

    Input: PR diff, acceptance criteria, code style guidelines
    Output: Detailed review with scores, specific feedback, line references
    """

    async def review_pr(
        self,
        pr_diff: str,
        acceptance_criteria: list[str],
        style_guide: dict
    ) -> ReviewResult:
        """
        Perform comprehensive code review.

        Analysis Areas:
        1. Code Quality (25 points)
           - Complexity, readability, naming
           - DRY principle, SOLID principles
           - Error handling patterns

        2. Security (25 points)
           - SQL injection, XSS, CSRF
           - Secrets in code
           - Input validation

        3. Testing (25 points)
           - Test coverage
           - Edge cases covered
           - Test quality (assertions, mocking)

        4. Documentation (15 points)
           - Docstrings, comments
           - README updates

        5. Acceptance Criteria (10 points)
           - Each criterion validated
           - Evidence from code changes

        Total: 100 points (≥80 for auto-approval)
        """
        pass
```

**Acceptance Criteria:**
- [ ] Agent analyzes actual code (not placeholders)
- [ ] Detects common security vulnerabilities (SQL injection, XSS, etc.)
- [ ] Validates each acceptance criterion with evidence
- [ ] Provides specific feedback with file:line references
- [ ] Scores correlate with real code quality
- [ ] Test suite shows catches 90%+ of intentional bugs

**Test Cases:**
```python
def test_security_vulnerability_detection():
    """Should detect SQL injection"""
    pr_diff = """
    + cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    """
    result = agent.review_pr(pr_diff, [], {})

    assert result.security_score < 15  # Low score
    assert any("sql injection" in issue.lower() for issue in result.issues)

def test_acceptance_criteria_validation():
    """Should verify criteria are actually met"""
    criteria = ["Add authentication middleware", "Hash passwords with bcrypt"]
    pr_diff = """
    + def authenticate(request):
    +     # TODO: Add auth logic
    +     pass
    """
    result = agent.review_pr(pr_diff, criteria, {})

    # Should fail - criteria not met
    assert result.acceptance_score < 5
    assert "not implemented" in result.feedback.lower()
```

**Estimated Duration:** 5 days

**Priority:** Critical - Review system is non-functional without this

---

#### Story 7.4: AI Analyzer Agents (6 Specialists)

**Objective:** Replace placeholder analyzers with functional AI-powered analysis

**Current Problem:**
```python
# All 6 analyzers in src/agents/analyzers/*.py return empty/placeholder results
# Ever-Thinker improvement engine is completely non-functional
```

**Why AI is Needed:**
- Performance, quality, testing, documentation, UX, architecture analysis require understanding
- Placeholder analyzers provide zero value
- Ever-Thinker cannot identify improvements without functional analyzers

**AI Agent Designs:**

##### 7.4.1: Performance Analyzer Agent

```python
class PerformanceAnalyzerAgent:
    """
    Analyzes code for performance issues.

    Detects:
    - O(n²) or worse algorithms where O(n) possible
    - N+1 query problems
    - Unnecessary loops/iterations
    - Inefficient data structures
    - Memory leaks
    """

    async def analyze(self, code: str, context: dict) -> list[Improvement]:
        """Returns specific performance improvement opportunities"""
        pass
```

##### 7.4.2: Code Quality Analyzer Agent

```python
class CodeQualityAnalyzerAgent:
    """
    Analyzes code quality and maintainability.

    Detects:
    - Code smells (long methods, god classes)
    - Complexity (cyclomatic complexity > 10)
    - Code duplication (DRY violations)
    - Poor naming conventions
    - Missing type hints
    """
    pass
```

##### 7.4.3: Testing Analyzer Agent

```python
class TestingAnalyzerAgent:
    """
    Analyzes test coverage and quality.

    Identifies:
    - Missing test cases
    - Uncovered edge cases
    - Low coverage areas
    - Poor test quality (no assertions, etc.)
    """
    pass
```

##### 7.4.4: Documentation Analyzer Agent

```python
class DocumentationAnalyzerAgent:
    """
    Analyzes documentation completeness.

    Finds:
    - Missing docstrings
    - Outdated documentation
    - Undocumented parameters
    - README gaps
    """
    pass
```

##### 7.4.5: UX Analyzer Agent

```python
class UXAnalyzerAgent:
    """
    Analyzes user experience.

    Evaluates:
    - CLI usability
    - Error message clarity
    - Help text quality
    - User workflows
    """
    pass
```

##### 7.4.6: Architecture Analyzer Agent

```python
class ArchitectureAnalyzerAgent:
    """
    Analyzes architectural concerns.

    Detects:
    - Tight coupling
    - Circular dependencies
    - Violation of separation of concerns
    - Scalability bottlenecks
    """
    pass
```

**Acceptance Criteria (All 6 Analyzers):**
- [ ] Each analyzer returns real findings (not empty/placeholder)
- [ ] Findings are specific with file:line references
- [ ] Suggestions are actionable
- [ ] Test suite shows 70%+ precision/recall on synthetic issues
- [ ] Integration with Ever-Thinker works
- [ ] Performance acceptable (< 5s per analyzer per codebase)

**Estimated Duration:** 8 days (all 6 analyzers)

**Priority:** Critical - Ever-Thinker is non-functional without these

---

### 🔥 HIGH PRIORITY AI AGENTS

#### Story 7.5: AI Error Recovery Agent

**Objective:** Replace fail-fast error handling with intelligent recovery

**Current Problem:**
```python
# src/executor.py:49-59
except Exception as e:
    task.status = TaskStatus.FAILED
    raise  # ❌ Stops entire execution, no recovery attempt
```

**Why AI is Needed:**
- Many errors are recoverable (missing imports, syntax errors, timeout)
- Could diagnose root cause and suggest fixes
- Could retry with alternative approaches
- Human intervention required for simple issues

**AI Agent Design:**

```python
class ErrorRecoveryAgent:
    """
    Intelligent error diagnosis and recovery.

    Input: Error context, task state, error history
    Output: Recovery strategy or actionable diagnosis
    """

    async def recover(self, error: Exception, context: dict) -> RecoveryStrategy:
        """
        Attempt intelligent error recovery.

        Steps:
        1. Classify error type (syntax, import, timeout, logic, etc.)
        2. Determine recoverability
        3. If recoverable:
           - Suggest specific fix
           - Retry with modified approach
           - Learn from error pattern
        4. If non-recoverable:
           - Provide clear diagnosis
           - Suggest manual intervention steps
        """
        pass
```

**Acceptance Criteria:**
- [ ] Classifies errors correctly (syntax, import, timeout, logic)
- [ ] Recovers from 60%+ of common errors (missing imports, syntax)
- [ ] Provides actionable fix suggestions for non-recoverable errors
- [ ] Learns from error patterns (doesn't repeat same error)
- [ ] Test suite shows recovery from 10+ error scenarios

**Estimated Duration:** 4 days

**Priority:** High - Significant UX improvement

---

#### Story 7.6: AI Backend Router Agent

**Objective:** Replace static backend selection with intelligent routing

**Current Problem:**
```python
# src/orchestrator.py:184-202
if backend_type == 'ccpm':
    return CCPMBackend(api_key)
elif backend_type == 'claude_code':
    return ClaudeCodeBackend(...)
# ❌ Static config, no intelligent routing
```

**Why AI is Needed:**
- Different tasks benefit from different backends
- Should route based on task complexity, type, cost/speed tradeoffs
- Should learn which backend works best for which tasks

**AI Agent Design:**

```python
class BackendRouterAgent:
    """
    Intelligent backend selection based on task characteristics.

    Input: Task description, complexity estimate, backend capabilities, historical performance
    Output: Optimal backend selection with reasoning
    """

    async def route(self, task: Task, available_backends: list[str]) -> BackendSelection:
        """
        Select optimal backend for task.

        Considerations:
        - Task complexity (simple → CCPM, complex → Claude Code)
        - Task type (refactoring → Claude Code, prototyping → CCPM)
        - Cost constraints
        - Speed requirements
        - Historical performance for similar tasks
        """
        pass
```

**Acceptance Criteria:**
- [ ] Routes simple tasks to fast/cheap backends (CCPM)
- [ ] Routes complex tasks to powerful backends (Claude Code)
- [ ] Considers cost/speed tradeoffs
- [ ] Learns from historical performance
- [ ] Test suite shows optimal routing in 80%+ cases

**Estimated Duration:** 3 days

**Priority:** High - Cost/quality optimization

---

#### Story 7.7: AI Improvement Engine Agent

**Objective:** Replace placeholder improvement engine with functional AI-powered system

**Current Problem:**
```python
# src/improvement_engine.py:43-122
improvements.append(Improvement(
    description="Add comprehensive error handling and logging",
    # ❌ Same generic suggestion for EVERY project
))
```

**Why AI is Needed:**
- Cannot identify project-specific improvements
- All analysis methods are empty placeholders
- Returns same suggestion regardless of code

**AI Agent Design:**

```python
class ImprovementEngineAgent:
    """
    Identifies project-specific improvement opportunities.

    Input: Generated code, task context, analyzer results, similar project patterns
    Output: Prioritized list of specific improvements
    """

    async def identify_improvements(
        self,
        code: str,
        analyzer_results: dict,
        project_context: dict
    ) -> list[Improvement]:
        """
        Identify actionable improvements.

        Uses results from:
        - Performance analyzer
        - Code quality analyzer
        - Testing analyzer
        - Documentation analyzer
        - UX analyzer
        - Architecture analyzer

        Prioritizes by:
        - Impact (critical bugs > optimization)
        - Effort (quick wins first)
        - Risk (safe changes before risky)
        """
        pass
```

**Acceptance Criteria:**
- [ ] Integrates with all 6 analyzer agents
- [ ] Returns project-specific improvements (not generic)
- [ ] Prioritizes correctly (impact × effort ÷ risk)
- [ ] Test suite shows relevant suggestions for 10+ projects

**Estimated Duration:** 3 days

**Priority:** High - Enables continuous improvement

---

### 📊 MEDIUM PRIORITY AI AGENTS

#### Story 7.8: AI Git Message Agents

**Objective:** Replace fixed templates with intelligent commit/PR message generation

**Current Problem:**
```python
# src/git_manager.py:93-106
return f"feat: {task.description[:60]}"  # ❌ Always "feat", always truncated

# src/git_manager.py:149-177
# Fixed PR template doesn't adapt to changes
```

**Why AI is Needed:**
- Cannot determine correct commit type (feat/fix/refactor/docs)
- Description truncation loses meaning
- PR descriptions don't summarize actual changes

**AI Agent Designs:**

##### 7.8.1: Commit Message Agent

```python
class CommitMessageAgent:
    """
    Generates optimal commit messages from code changes.

    Input: Code diff, task context, project conventions
    Output: Conventional commit message following project standards
    """

    async def generate_commit_message(
        self,
        diff: str,
        task: Task,
        conventions: dict
    ) -> str:
        """
        Generate commit message.

        Steps:
        1. Analyze diff to determine type (feat/fix/refactor/docs/test)
        2. Summarize changes meaningfully (not truncated)
        3. Follow conventional commits or project style
        4. Add relevant references (issue numbers, etc.)
        """
        pass
```

##### 7.8.2: PR Description Agent

```python
class PRDescriptionAgent:
    """
    Generates comprehensive PR descriptions optimized for review.

    Input: Code diff, task context, acceptance criteria
    Output: Detailed PR description with context
    """
    pass
```

**Acceptance Criteria:**
- [ ] Determines correct commit type (90%+ accuracy)
- [ ] Summaries are meaningful (not truncated)
- [ ] Follows conventional commits format
- [ ] PR descriptions include change summary, testing instructions, context

**Estimated Duration:** 2 days

**Priority:** Medium - Quality of life improvement

---

#### Story 7.9: AI Pattern Learning Agents

**Objective:** Replace fixed thresholds with adaptive pattern recognition

**Current Problem:**
```python
# src/learning/pattern_detector.py:50-67
self._similarity_threshold = 0.8  # ❌ Fixed for all pattern types

# src/learning/pattern_detector.py:288-395
# Simple string splitting for pattern extraction
```

**Why AI is Needed:**
- Different pattern types need different thresholds
- Cannot understand semantic similarity
- Misses complex patterns

**AI Agent Designs:**

##### 7.9.1: Pattern Extraction Agent

```python
class PatternExtractionAgent:
    """
    Extracts meaningful patterns from outcomes.

    Input: Outcome data, context
    Output: Structured pattern data with semantic understanding
    """
    pass
```

##### 7.9.2: Pattern Matching Agent

```python
class PatternMatchingAgent:
    """
    Matches patterns with adaptive thresholds.

    Input: Candidate patterns, historical patterns, context
    Output: Matched patterns with confidence scores
    """
    pass
```

**Acceptance Criteria:**
- [ ] Semantic similarity understanding (not just string matching)
- [ ] Adaptive thresholds per pattern type
- [ ] Learns from match outcomes
- [ ] 80%+ precision/recall on pattern matching tests

**Estimated Duration:** 3 days

**Priority:** Medium - Long-term learning foundation

---

#### Story 7.10: AI Configuration Intelligence Agent

**Objective:** Add intelligent config validation and suggestions

**Current Problem:**
```python
# src/config_validator.py:48-68
VALID_PERSPECTIVES = ["performance", "code_quality", ...]  # ❌ Hardcoded
# Cannot suggest alternatives for invalid values
```

**AI Agent Design:**

```python
class ConfigIntelligenceAgent:
    """
    Intelligent configuration validation and optimization.

    Input: Configuration, context, available tools
    Output: Validation with suggestions and auto-correction
    """
    pass
```

**Acceptance Criteria:**
- [ ] Suggests corrections for invalid values
- [ ] Detects semantic issues
- [ ] Recommends optimal configurations
- [ ] Auto-discovers available tools

**Estimated Duration:** 2 days

**Priority:** Medium - User experience improvement

---

#### Story 7.11: AI Timeout/Resource Estimator Agent

**Objective:** Replace fixed timeouts with intelligent estimation

**Current Problem:**
```python
# src/backend.py:115-124
self.timeout_s = 900  # ❌ Fixed 15 minutes for all tasks
```

**AI Agent Design:**

```python
class ResourceEstimatorAgent:
    """
    Estimates optimal resource allocation for tasks.

    Input: Task complexity, historical performance
    Output: Optimized resource allocation (timeout, memory)
    """
    pass
```

**Acceptance Criteria:**
- [ ] Estimates vary by task complexity
- [ ] Learns from historical execution times
- [ ] Reduces timeout failures by 50%+

**Estimated Duration:** 2 days

**Priority:** Medium - Resource optimization

---

## Implementation Timeline

### Phase 1: Foundation (Week 1)
**Days 1-3: Story 7.1 - Repository Isolation (CRITICAL)**
- Implement `--target` flag
- Create `.moderator/` directory structure
- Configuration cascade
- Multi-project isolation
- Validation suite

**Days 4-7: Infrastructure for AI Agents**
- LLM integration framework
- Agent base class
- Prompt templates
- Response parsing
- Error handling

### Phase 2: Critical AI Agents (Weeks 2-3)
**Week 2:**
- Story 7.2: Task Decomposition Agent (4 days)
- Story 7.3: Code Review Agent (3 days)

**Week 3:**
- Story 7.4: All 6 Analyzer Agents (8 days total)
  - Performance (1 day)
  - Code Quality (2 days)
  - Testing (1 day)
  - Documentation (1 day)
  - UX (1 day)
  - Architecture (2 days)

### Phase 3: High Priority AI Agents (Week 4)
- Story 7.5: Error Recovery Agent (4 days)
- Story 7.6: Backend Router Agent (3 days)

### Phase 4: Improvement Engine (Week 5)
- Story 7.7: Improvement Engine Agent (3 days)
- Integration testing (2 days)

### Phase 5: Medium Priority Agents (Week 6)
- Story 7.8: Git Message Agents (2 days)
- Story 7.9: Pattern Learning Agents (3 days)
- Story 7.10: Config Intelligence Agent (2 days)

### Buffer & Polish (Remaining Days)
- Story 7.11: Resource Estimator Agent
- Documentation
- End-to-end testing
- Performance optimization

**Total Timeline: 6 weeks (42 days)**

---

## Architecture Changes

### New Components

```
src/
├── agents/
│   ├── base_agent.py                    # Base class for all AI agents
│   ├── decomposition_agent.py           # Story 7.2
│   ├── code_review_agent.py             # Story 7.3
│   ├── error_recovery_agent.py          # Story 7.5
│   ├── backend_router_agent.py          # Story 7.6
│   ├── improvement_engine_agent.py      # Story 7.7
│   ├── commit_message_agent.py          # Story 7.8.1
│   ├── pr_description_agent.py          # Story 7.8.2
│   ├── pattern_extraction_agent.py      # Story 7.9.1
│   ├── pattern_matching_agent.py        # Story 7.9.2
│   ├── config_intelligence_agent.py     # Story 7.10
│   ├── resource_estimator_agent.py      # Story 7.11
│   └── analyzers/                       # Story 7.4 (all refactored)
│       ├── performance_analyzer_agent.py
│       ├── code_quality_analyzer_agent.py
│       ├── testing_analyzer_agent.py
│       ├── documentation_analyzer_agent.py
│       ├── ux_analyzer_agent.py
│       └── architecture_analyzer_agent.py
├── llm/
│   ├── provider.py                      # LLM provider abstraction
│   ├── prompts.py                       # Prompt templates
│   ├── parser.py                        # Response parsing
│   └── cache.py                         # Response caching
└── config_loader.py                     # Story 7.1 (NEW)
```

### Modified Components

```
main.py                    # Add --target flag (Story 7.1)
src/state_manager.py       # Use .moderator/ directory (Story 7.1)
src/git_manager.py         # Use target repo (Story 7.1)
src/orchestrator.py        # Integrate all AI agents
src/decomposer.py          # Replace with AI agent (Story 7.2)
src/pr_reviewer.py         # Replace with AI agent (Story 7.3)
src/executor.py            # Integrate error recovery (Story 7.5)
src/backend.py             # Integrate router & estimator (Story 7.6, 7.11)
src/improvement_engine.py  # Replace with AI agent (Story 7.7)
```

---

## Success Criteria

### Functional Requirements

✅ **Repository Isolation (Story 7.1):**
- [ ] Can work on unlimited projects simultaneously
- [ ] Tool repository stays clean (no state pollution)
- [ ] Multi-project isolation tests pass
- [ ] Backward compatibility maintained

✅ **Task Decomposition (Story 7.2):**
- [ ] Task structure varies by project type
- [ ] 80%+ improvement over template-based approach
- [ ] Acceptance criteria specific to requirements

✅ **Code Review (Story 7.3):**
- [ ] Catches 90%+ of intentional bugs in tests
- [ ] Provides specific feedback with line references
- [ ] Scores correlate with real code quality

✅ **Analyzers (Story 7.4):**
- [ ] All 6 analyzers return real findings
- [ ] 70%+ precision/recall on synthetic issues
- [ ] Ever-Thinker integration works

✅ **Error Recovery (Story 7.5):**
- [ ] Recovers from 60%+ of common errors
- [ ] Actionable fix suggestions for non-recoverable errors
- [ ] Learns from error patterns

✅ **Backend Router (Story 7.6):**
- [ ] Optimal routing in 80%+ of cases
- [ ] Learns from historical performance

✅ **Improvement Engine (Story 7.7):**
- [ ] Project-specific improvements (not generic)
- [ ] Prioritizes correctly

### Quality Requirements

- [ ] All AI agents have 80%+ test coverage
- [ ] End-to-end tests pass for complete workflows
- [ ] Performance acceptable (< 30s for full decomposition)
- [ ] Cost acceptable (< $1 per project for AI calls)

### User Experience Requirements

- [ ] Clear error messages with fix suggestions
- [ ] Transparent AI reasoning (explain decisions)
- [ ] Graceful degradation if LLM unavailable
- [ ] Documentation for all AI agents

---

## Risks & Mitigations

### Risk 1: LLM Cost Explosion

**Risk:** AI agents make too many LLM calls → high cost

**Mitigation:**
- Response caching (same prompt = cached result)
- Batch processing where possible
- Use smaller models for simple tasks (Haiku for classification, Sonnet for complex)
- Monitor costs per project
- Set cost budgets and alerts

### Risk 2: LLM Latency

**Risk:** AI agents too slow → poor UX

**Mitigation:**
- Parallel agent execution where possible
- Stream responses for long-running operations
- Use fast models for time-sensitive operations
- Cache common patterns
- Show progress indicators

### Risk 3: AI Agent Quality

**Risk:** AI agents make poor decisions → bad outcomes

**Mitigation:**
- Comprehensive test suites for each agent
- Human-in-the-loop for critical decisions (PRs, improvements)
- Confidence scores on all AI outputs
- Fallback to deterministic logic if confidence low
- A/B testing against current approach

### Risk 4: Architectural Fix Regression

**Risk:** Story 7.1 breaks existing functionality

**Mitigation:**
- Comprehensive validation suite
- Backward compatibility maintained
- Phased rollout (Week 1 only Story 7.1)
- No new features until validation passes

### Risk 5: Scope Creep

**Risk:** 23 AI agents is too much for 6 weeks

**Mitigation:**
- Clear prioritization (Critical → High → Medium)
- MVP for each agent (can enhance later)
- Weekly checkpoints
- Cut medium-priority agents if needed

---

## Dependencies

### Blocked By:
- Gear 1 completion (DONE ✅)

### Blocks:
- Gear 3 (Ever-Thinker continuous improvement)
- Gear 4 (Multi-project orchestration at scale)

### External Dependencies:
- LLM API access (Claude, GPT-4, etc.)
- Git repository (target must be git-initialized)

---

## Documentation Artifacts

Upon completion, the following documentation will be created/updated:

1. **Implementation Guides:**
   - `docs/agents/ai-agent-framework.md` - Framework for building AI agents
   - `docs/agents/prompt-engineering-guide.md` - Best practices for agent prompts
   - `docs/agents/testing-ai-agents.md` - Testing strategies

2. **Architecture Updates:**
   - `docs/diagrams/ai-agent-architecture.md` - AI agent system architecture
   - `docs/diagrams/repository-isolation.md` - Multi-project isolation architecture
   - Update `docs/archetcture.md` with AI agent integration

3. **User Documentation:**
   - Update `README.md` with `--target` flag usage
   - `docs/guides/multi-project-usage.md` - Using Moderator on multiple projects
   - `docs/guides/ai-agent-customization.md` - Customizing AI agent behavior

4. **Development Documentation:**
   - Update `CLAUDE.md` with Epic 7 information
   - `docs/epics/epic-7-retrospective.md` - Lessons learned
   - `docs/epics/epic-7-metrics.md` - Performance and cost metrics

---

## Metrics & KPIs

### Success Metrics

| Metric | Baseline (Gear 1) | Target (Epic 7) | Measurement |
|--------|------------------|-----------------|-------------|
| Multi-project support | ❌ Not possible | ✅ Unlimited | Multi-project isolation tests |
| Task decomposition quality | Template (static) | AI-generated (adaptive) | User survey: relevance score |
| PR review accuracy | 0% (fake scores) | 90%+ bug detection | Synthetic bug injection tests |
| Error recovery rate | 0% (fail-fast) | 60%+ | Error recovery tests |
| Improvement relevance | 0% (generic) | 80%+ specific | User survey: usefulness score |
| Time to first PR | 15-20 min | 10-15 min | End-to-end benchmarks |
| Human intervention rate | 3-5 per project | 1-2 per project | Workflow tracking |

### Cost Metrics

| Item | Estimated Cost | Acceptable Range |
|------|---------------|------------------|
| LLM calls per project | $0.50-$1.00 | $0.25-$2.00 |
| Development time | 42 days | 35-50 days |

### Quality Metrics

| Item | Target | Measurement |
|------|--------|-------------|
| Test coverage | 80%+ | pytest --cov |
| AI agent accuracy | 70-90% | Synthetic test suites |
| User satisfaction | 4/5 stars | User surveys |

---

## Conclusion

Epic 7 transforms Moderator from a deterministic orchestration tool into an intelligent AI-powered system by:

1. **Fixing the critical architectural flaw** (Story 7.1) - enables multi-project support
2. **Replacing 23 naive logic points** with intelligent AI agents
3. **Building foundation for continuous learning** (pattern recognition, improvement cycles)

**Critical Success Factors:**
- Story 7.1 MUST be completed first and validated before proceeding
- AI agents must be tested comprehensively (avoid "fake" implementations)
- Cost and latency must be monitored continuously
- Phased rollout with validation gates

**Next Steps:**
1. Review and approve this epic plan
2. Create detailed technical specifications for Story 7.1
3. Begin Week 1: Repository isolation implementation
4. Validate Week 1 before proceeding to AI agents

---

**Epic Owner:** Development Team
**Stakeholders:** Product, Engineering, Users
**Status:** Planning → Awaiting Approval

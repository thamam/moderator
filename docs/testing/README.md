# Moderator Testing Documentation

**Purpose:** Test the complete Moderator framework (Gears 1-4, Epics 1-7) using a real-world project

**Created:** 2025-01-16

---

## Testing Philosophy

The goal is NOT to build the CLI tool ourselves, but to **TEST if Moderator can autonomously build it from a minimal seed input**.

### Approach

1. **Minimal Input:** Give Moderator only a problem statement (see `moderator-seed-input.txt`)
2. **Autonomous Discovery:** Let Moderator discover data locations, design architecture, implement code
3. **Answer Keys:** Use our Phase 1 documents as validation references
4. **Observational Testing:** Monitor with 5 checkpoints, not build the tool ourselves
5. **Iterative Improvement:** Expect failures, analyze, fix Moderator, re-run

---

## Documents in This Directory

### Test Execution Documents

1. **`instrumented-test-plan.md`** - Comprehensive test plan with 5 checkpoints
   - Phase 0-6 execution protocol
   - Checkpoint specifications and scoring rubrics
   - Results documentation templates
   - Success metrics and iteration strategy

2. **`moderator-test-sequence-diagram.md`** - Visual representation of test flow
   - Mermaid sequence diagram showing all 6 phases
   - Checkpoint markers (📍 CP1-5) clearly indicated
   - Alert level flowchart (🟢/🟡/🔴)
   - Timing breakdown (4.5 hour first run estimate)

### Checkpoint Implementation Scripts

3. **`checkpoint-1-validator.sh`** - Problem Understanding
   - Counts clarifying questions asked by Moderator
   - Pass criteria: ≥3 questions
   - Score: /20 points

4. **`checkpoint-2-validator.sh`** - Discovery Validation
   - Compares discovered locations to answer key
   - Checks: Data location (40), File format (30), Security (20), Data size (10)
   - Pass criteria: ≥60/100 points

5. **`checkpoint-3-evaluator.sh`** - Architecture Quality (Interactive)
   - Human-scored rubric evaluation
   - Categories: Topology (30), Cross-platform (25), Conflicts (25), Security (20)
   - Pass criteria: ≥60/100 points

6. **`checkpoint-4-qa-gates.sh`** - Code Quality (Epic 4 Validation)
   - Runs Bandit, Pylint, Flake8 on generated code
   - Pass criteria: Bandit catches ≥1 issue (proves QA works)

7. **`checkpoint-5-coverage.sh`** - Test Coverage
   - Runs pytest --cov on generated code
   - Pass criteria: ≥60% coverage (Target: ≥80%)

### Input and Answer Keys

8. **`moderator-seed-input.txt`** - Minimal problem statement for Moderator
   - Only describes the problem, no solutions
   - No architecture, no schemas, no hints

9. **`claude-data-schema.md`** - Answer key for Checkpoint 2 (Discovery)
   - Comprehensive documentation of Claude Code data structure
   - Created during our Phase 1 discovery work

10. **`claude-sync-architecture.md`** - Answer key for Checkpoint 3 (Architecture)
    - 13-section architecture document
    - Hub-and-spoke design with rsync over SSH
    - Created during our Phase 1 architecture work

11. **`claude-sync-prd.md`** - Answer key for requirements coverage
    - 12-section PRD with epics and user stories
    - Created during our Phase 1 requirements work

---

## Quick Start Guide

### Phase 0: Setup Instrumentation (15 minutes)

```bash
# 1. Ensure all checkpoint scripts are executable
chmod +x docs/testing/checkpoint-*.sh

# 2. Install QA tools if not already installed
pip install bandit pylint flake8 pytest pytest-cov

# 3. Prepare monitoring
# Create a terminal split to watch logs in real-time
```

### Phase 1: Execute Moderator Test

```bash
# Start Moderator with minimal seed input
cd /home/thh3/personal/moderator
python main.py "$(cat docs/testing/moderator-seed-input.txt)"

# In separate terminal: Monitor execution
tail -f state/proj_*/logs.jsonl
```

### Phase 2: Run Checkpoints

As Moderator progresses through phases, run checkpoints:

```bash
# Checkpoint 1: After Moderator asks questions
./docs/testing/checkpoint-1-validator.sh moderator-conversation.log

# Checkpoint 2: After discovery phase
./docs/testing/checkpoint-2-validator.sh state/proj_*/discovery-output.md

# Checkpoint 3: After architecture phase
./docs/testing/checkpoint-3-evaluator.sh state/proj_*/architecture.md

# Checkpoint 4: After code generation (automatic via Epic 4)
./docs/testing/checkpoint-4-qa-gates.sh state/proj_*/artifacts/task_*/generated/

# Checkpoint 5: After implementation complete
./docs/testing/checkpoint-5-coverage.sh state/proj_*/artifacts/task_*/generated/
```

### Phase 3: Analyze Results

```bash
# Review all checkpoint results
cat checkpoint-*-results.txt

# Calculate overall score
echo "CP1: $(grep 'Score:' checkpoint-1-results.txt)"
echo "CP2: $(grep 'Score:' checkpoint-2-results.txt)"
echo "CP3: $(grep 'Score:' checkpoint-3-results.txt)"
echo "CP4: $(grep 'Status:' checkpoint-4-results.txt)"
echo "CP5: $(grep 'Coverage:' checkpoint-5-results.txt)"
```

---

## Success Criteria

| Checkpoint | Minimum | Target | Stretch |
|------------|---------|--------|---------|
| CP1 | 10/20 (3 questions) | 15/20 (5 questions) | 20/20 (insightful) |
| CP2 | 60/100 | 75/100 | 90/100 |
| CP3 | 60/100 | 80/100 | 95/100 |
| CP4 | Bandit catches 1 issue | All gates pass | Perfect scores |
| CP5 | 60% coverage | 80% coverage | 95% coverage |

**Overall Success Levels:**

- **Minimum:** 3/5 checkpoints at "Minimum", code runs
- **Target:** 4/5 checkpoints at "Target", tool partially works
- **Stretch:** 5/5 checkpoints at "Stretch", tool fully solves problem

**Expected First Run:** Minimum to Target

---

## Alert System

**🟢 INFO (Continue):**
- Checkpoint passed
- Expected behavior
- Progress milestone

**🟡 WARNING (Monitor):**
- Checkpoint marginal (60-79 score)
- Slow progress (>2x estimated time)
- Minor QA issues (warnings)

**🔴 CRITICAL (Intervene):**
- Checkpoint failed (<60 score)
- Stuck (3+ retries same task)
- Security issue unaddressed
- Architecture fundamentally flawed
- Dangerous operation (file deletion, sudo)

---

## Iteration Loop

```
Run #1 (expect failures)
   ↓
Analyze checkpoint results
   ↓
Identify top 3 root causes
   ↓
Fix Moderator framework
   ↓
Run #2
   ↓
Compare scores (improvement?)
   ↓
Repeat until Target success achieved
```

**Exit Criteria:**
- ✅ Target success achieved (4/5 checkpoints at Target level)
- ✅ Tool solves actual problem in practice
- ❌ OR: Diminishing returns (3+ runs with no improvement)

---

## Expected Timeline

**First Run (Baseline):**
- Phase 0 (Setup): 15 minutes
- Phase 1 (Seed + Questions): 10 minutes
- Phase 2 (Discovery): 45 minutes
- Phase 3 (Architecture): 65 minutes
- Phase 4 (Implementation): 185 minutes
- Phase 5 (Ever-Thinker): 30 minutes
- Phase 6 (Analysis): 30 minutes

**Total:** ~6 hours

**Subsequent Runs:** Expect faster execution as Moderator improves (3-4 hours)

---

## Key Learnings to Document

After each run, document:

1. **What worked well** - Which components exceeded expectations?
2. **What failed** - Which checkpoints failed and why?
3. **Root causes** - Top 3 issues to fix in Moderator
4. **Unexpected behaviors** - Anything surprising (good or bad)?
5. **Next iteration plan** - Specific changes to make before Run #2

---

## Files Generated During Test

**Checkpoint Results:**
- `checkpoint-1-results.txt` - Problem understanding scores
- `checkpoint-2-results.txt` - Discovery validation scores
- `checkpoint-3-results.txt` - Architecture quality scores
- `checkpoint-4-results.txt` - QA gates results
- `checkpoint-5-results.txt` - Test coverage results

**Detailed Reports:**
- `checkpoint-4-bandit-report.txt` - Security scan details
- `checkpoint-4-pylint-report.txt` - Code quality details
- `checkpoint-4-flake8-report.txt` - Style check details
- `checkpoint-5-pytest-output.txt` - Test execution log

**Moderator Artifacts:**
- `state/proj_*/project.json` - Project state
- `state/proj_*/logs.jsonl` - Execution logs
- `state/proj_*/artifacts/` - Generated code

---

## Next Steps

1. **Review this README** - Ensure you understand the testing approach
2. **Review test plan** - Read `instrumented-test-plan.md` for full details
3. **Review sequence diagram** - Visualize flow in `moderator-test-sequence-diagram.md`
4. **Execute Phase 0** - Set up instrumentation
5. **Run Moderator test** - Start with minimal seed input
6. **Monitor with checkpoints** - Validate as it progresses
7. **Analyze and iterate** - Fix issues, re-run, improve

---

**Document Version:** 1.0
**Created:** 2025-01-16
**Status:** Ready for execution

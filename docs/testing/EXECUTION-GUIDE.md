# Moderator Test Execution Guide

**Purpose:** Step-by-step guide for executing the instrumented Moderator test

**Created:** 2025-01-16

---

## Phase 0: Setup Instrumentation (15 minutes)

### Step 0.1: Verify Prerequisites

```bash
# Check Python and dependencies
python --version  # Should be 3.9+
pip list | grep -E "pytest|bandit|pylint|flake8"

# Install if missing
pip install pytest pytest-cov bandit pylint flake8
```

### Step 0.2: Verify Checkpoint Scripts

```bash
# Navigate to testing directory
cd /home/thh3/personal/moderator/docs/testing

# Verify all scripts exist and are executable
ls -la checkpoint-*.sh

# Expected output:
# -rwxr-xr-x checkpoint-1-validator.sh
# -rwxr-xr-x checkpoint-2-validator.sh
# -rwxr-xr-x checkpoint-3-evaluator.sh
# -rwxr-xr-x checkpoint-4-qa-gates.sh
# -rwxr-xr-x checkpoint-5-coverage.sh

# If not executable, run:
chmod +x checkpoint-*.sh
```

### Step 0.3: Verify Answer Key Files

```bash
# Check answer key files exist
ls -la claude-*.md

# Expected output:
# claude-data-schema.md
# claude-sync-architecture.md
# claude-sync-prd.md
```

### Step 0.4: Verify Seed Input

```bash
# Check seed input file
cat moderator-seed-input.txt

# Should contain minimal problem statement
# NO architecture details, NO solutions, just the problem
```

### Step 0.5: Setup Monitoring

```bash
# Create results directory
mkdir -p test-results
cd test-results

# Open monitoring terminal (split screen or new terminal)
# Terminal 1: Main execution (you'll start Moderator here)
# Terminal 2: Log monitoring (tail logs in real-time)
# Terminal 3: Checkpoint running (run validation scripts)
```

### Step 0.6: Pre-Execution Checklist

- [ ] Python 3.9+ installed
- [ ] pytest, bandit, pylint, flake8 installed
- [ ] All 5 checkpoint scripts executable
- [ ] Answer key files in place
- [ ] Seed input file ready
- [ ] Results directory created
- [ ] 3 terminal windows ready (main, logs, checkpoints)
- [ ] 4-6 hours allocated
- [ ] Notepad ready for observations

---

## Phase 1: Seed Moderator (5 minutes)

### Step 1.1: Start Moderator with Seed Input

**Terminal 1 (Main Execution):**

```bash
# Navigate to Moderator root directory
cd /home/thh3/personal/moderator

# Start Moderator with seed input
python main.py "$(cat docs/testing/moderator-seed-input.txt)"
```

**What Moderator receives:**
```
Problem: Claude Code Conversation Sync Across Multiple Machines

I work with Claude Code CLI across 4 machines:
- XPS (Linux, 192.168.68.62, user: thh3) - always on
- ROG (Linux, 192.168.68.65, user: thh3)
- MAC (macOS, 192.168.68.56, user: tomerhamam)
- NELLY (Windows, 192.168.68.60, user: nelly)

All machines are on my local network with passwordless SSH already configured.

Current Pain:
When I switch from one machine to another, I lose my Claude Code conversation
history and context. I have to re-explain everything to Claude, which wastes time.

Goal:
Build a tool that automatically synchronizes my Claude Code conversations and
project context across all 4 machines, so I can seamlessly continue work on
any machine.

Bonus Feature:
It would also be useful to have a unified dashboard showing all my GitHub pull
requests across repositories in one place.

Requirements:
- Automatic sync (no manual intervention)
- Fast sync (within seconds of making changes)
- Works across Linux, macOS, and Windows
- Safe (no data loss)

That's all I can provide. Please investigate, design, and implement this tool.
```

### Step 1.2: Monitor Moderator's Initial Response

**Terminal 2 (Log Monitoring):**

```bash
# Watch Moderator logs in real-time
tail -f state/proj_*/logs.jsonl
```

### Step 1.3: Capture Moderator's Questions

**What to watch for:**
- Moderator should ask clarifying questions
- Capture ALL questions asked in the first 5-10 minutes

**Create conversation log:**

```bash
# In Terminal 3 (Checkpoints)
cd /home/thh3/personal/moderator/docs/testing/test-results

# Capture Moderator's output to file
# Copy-paste Moderator's initial questions into:
vim moderator-conversation.log

# OR if Moderator provides a session file, copy it:
# cp /path/to/moderator/session.log moderator-conversation.log
```

### Step 1.4: Run Checkpoint 1 (Problem Understanding)

**After Moderator finishes asking questions (5-10 min):**

```bash
# Terminal 3 (Checkpoints)
cd /home/thh3/personal/moderator/docs/testing

# Run Checkpoint 1 validator
./checkpoint-1-validator.sh test-results/moderator-conversation.log

# Follow interactive prompts to assess question quality
# Script will:
#   1. Count questions automatically
#   2. Ask you to count clarifying questions
#   3. Ask you to count insightful questions
#   4. Calculate score
#   5. Save results to checkpoint-1-results.txt
```

**Expected questions from Moderator:**
- Where is Claude Code data stored? (filesystem paths)
- Are all machines always reachable?
- What's the acceptable sync latency?
- Should API credentials be synchronized?
- What happens if same conversation modified on 2 machines?

**Alert Triggers:**
- 🟢 PASS: ≥5 questions, mostly clarifying
- 🟡 WARNING: 3-4 questions, some superficial
- 🔴 FAIL: <3 questions or all superficial

### Step 1.5: Provide Answers to Moderator

**After Checkpoint 1 completes, answer Moderator's questions:**

If Moderator asks where data is stored:
> "I don't know exactly - you'll need to investigate on each machine."

If Moderator asks about sync latency:
> "Within seconds would be ideal, but up to 10 seconds is acceptable."

If Moderator asks about credentials:
> "API credentials should NOT be synchronized - too risky."

**Key principle:** Provide answers but NO solutions. Don't tell Moderator HOW to solve it.

---

## Phase 2: Discovery (30-60 minutes)

### Step 2.1: Monitor Discovery Phase

**Terminal 2 (Logs):**
```bash
# Watch for SSH commands, file searches
tail -f state/proj_*/logs.jsonl | grep -E "ssh|find|ls|du"
```

**What Moderator should do:**
1. SSH to each of the 4 machines
2. Search for Claude Code data locations
3. Examine file formats (JSONL, JSON)
4. Measure data sizes
5. Identify security concerns (.credentials.json)

**What to observe:**
- Does Moderator SSH to all 4 machines?
- Does Moderator find `~/.claude/` directory?
- Does Moderator check file formats?
- Does Moderator notice `.credentials.json`?

### Step 2.2: Capture Discovery Output

**When Moderator completes discovery (30-60 min), it should produce a discovery document:**

```bash
# Check for discovery output
ls -la state/proj_*/artifacts/

# Look for discovery document (may be named differently)
# Examples: discovery-report.md, data-schema.md, investigation-findings.md
```

**If Moderator creates the document:**
```bash
# Copy to test-results for validation
cp state/proj_*/artifacts/discovery-output.md test-results/
```

**If Moderator doesn't create a document:**
```bash
# Extract discovery findings from logs
grep -A 50 "discovery\|investigation\|found" state/proj_*/logs.jsonl > test-results/discovery-output.md
```

### Step 2.3: Run Checkpoint 2 (Discovery Validation)

```bash
# Terminal 3 (Checkpoints)
cd /home/thh3/personal/moderator/docs/testing

# Run Checkpoint 2 validator
./checkpoint-2-validator.sh test-results/discovery-output.md

# Script will automatically check:
#   1. Found .claude/ on all 4 machines (40 pts)
#   2. Identified JSONL + JSON formats (30 pts)
#   3. Flagged .credentials.json risk (20 pts)
#   4. Measured data size ~824MB (10 pts)
#
# Total: /100 points
# Pass: ≥60 points
```

**Alert Triggers:**
- 🟢 EXCELLENT: ≥90 points
- 🟢 PASS (TARGET): ≥75 points
- 🟡 PASS (MINIMUM): ≥60 points
- 🔴 FAIL: <60 points

**If Checkpoint 2 fails (<60 points):**
- Log the failure
- DO NOT intervene (let Moderator proceed with incomplete discovery)
- Document what was missed

---

## Phase 3: Architecture Design (30-60 minutes)

### Step 3.1: Monitor Architecture Phase

**Terminal 2 (Logs):**
```bash
# Watch for architecture design activities
tail -f state/proj_*/logs.jsonl | grep -E "architecture|design|topology"
```

**What Moderator should do:**
1. Propose system architecture (hub-and-spoke, peer-to-peer, etc.)
2. Choose sync protocol (rsync, custom daemon, etc.)
3. Design conflict resolution strategy
4. Address cross-platform differences (Linux/Mac/Windows)
5. Plan security measures

### Step 3.2: Capture Architecture Document

```bash
# Check for architecture document
ls -la state/proj_*/artifacts/

# Look for: architecture.md, system-design.md, technical-spec.md
```

**Copy architecture document:**
```bash
cp state/proj_*/artifacts/architecture.md test-results/
```

### Step 3.3: Run Checkpoint 3 (Architecture Quality)

```bash
# Terminal 3 (Checkpoints)
cd /home/thh3/personal/moderator/docs/testing

# Run Checkpoint 3 evaluator (INTERACTIVE)
./checkpoint-3-evaluator.sh test-results/architecture.md

# You'll be asked to score 4 categories:
#
# 1. Topology Choice (30 pts):
#    - Is hub-and-spoke, peer-to-peer, or other topology viable?
#    - Select: 1=Sensible (30), 2=Workable (15), 3=Flawed (0)
#
# 2. Cross-Platform (25 pts):
#    - Does it address Linux/Mac/Windows differences?
#    - Select: 1=Comprehensive (25), 2=Mentioned (15), 3=Assumes single (10), 4=Ignores (0)
#
# 3. Conflict Resolution (25 pts):
#    - Does it have a conflict strategy?
#    - Select: 1=Clear strategy (25), 2=Has strategy (15), 3=Acknowledges (5), 4=No mention (0)
#
# 4. Security (20 pts):
#    - Does it address .credentials.json, SSH, encryption?
#    - Select: 1=Comprehensive (20), 2=Credentials flagged (15), 3=Generic (10), 4=None (0)
#
# Total: /100 points
# Pass: ≥60 points
```

**Alert Triggers:**
- 🟢 EXCELLENT: ≥95 points
- 🟢 PASS (TARGET): ≥80 points
- 🟡 PASS (MINIMUM): ≥60 points
- 🔴 FAIL: <60 points

**Compare to answer key:**
```bash
# Review our answer key for reference
less claude-sync-architecture.md

# Compare Moderator's approach to our approach
# Note similarities and differences
```

---

## Phase 4: Implementation (2-4 hours)

### Step 4.1: Monitor Implementation Phase

**Terminal 2 (Logs):**
```bash
# Watch for code generation
tail -f state/proj_*/logs.jsonl | grep -E "generated|created|implemented"
```

**What Moderator should do:**
1. Generate sync daemon code
2. Write unit tests
3. QA gates auto-run on each file (Epic 4)
4. Fix any security issues caught by Bandit

**What to observe:**
- Are QA tools (Bandit/Pylint/Flake8) running automatically?
- Is Moderator fixing issues caught by QA tools?
- Are tests being written?

### Step 4.2: Run Checkpoint 4 (QA Gates) - Real-Time

**As code is generated, run Checkpoint 4:**

```bash
# Terminal 3 (Checkpoints)
cd /home/thh3/personal/moderator/docs/testing

# Run Checkpoint 4 on generated code directory
./checkpoint-4-qa-gates.sh ../../../state/proj_*/artifacts/task_*/generated/

# Script will run:
#   1. Bandit (security scanner)
#   2. Pylint (code quality)
#   3. Flake8 (PEP 8 style)
#
# PASS criteria: Bandit catches ≥1 security issue
# This validates Epic 4 (QA Integration) is working!
```

**Expected results:**
- Bandit should catch command injection, hardcoded secrets, etc.
- Pylint should score 7-9/10 (some issues expected on first run)
- Flake8 should find PEP 8 violations

**Alert Triggers:**
- 🟢 PASS: Bandit caught ≥1 issue (Epic 4 works!)
- 🟡 MARGINAL: Bandit found 0 issues (Epic 4 may not be working)

### Step 4.3: Run Checkpoint 5 (Test Coverage) - After Implementation

**When Moderator completes implementation:**

```bash
# Terminal 3 (Checkpoints)
cd /home/thh3/personal/moderator/docs/testing

# Run Checkpoint 5 on generated code directory
./checkpoint-5-coverage.sh ../../../state/proj_*/artifacts/task_*/generated/

# Script will:
#   1. Find test files (test_*.py)
#   2. Run pytest --cov
#   3. Measure coverage percentage
#   4. Check if tests pass
#
# PASS criteria: ≥60% coverage (Target: ≥80%)
```

**Alert Triggers:**
- 🟢 EXCELLENT: ≥95% coverage
- 🟢 PASS (TARGET): ≥80% coverage
- 🟡 PASS (MINIMUM): ≥60% coverage
- 🔴 FAIL: <60% coverage OR tests failing

---

## Phase 5: Ever-Thinker Analysis (30 minutes)

### Step 5.1: Trigger Ever-Thinker

**If Epic 3 (Ever-Thinker) is implemented:**

```bash
# Run Ever-Thinker on completed code
python -m src.ever_thinker --project state/proj_*/

# Ever-Thinker should analyze code from multiple angles:
#   - Performance optimizations
#   - Code quality improvements
#   - Security enhancements
#   - Testing gaps
#   - Documentation needs
#   - Architecture improvements
```

### Step 5.2: Review Suggestions

**Capture Ever-Thinker output:**
```bash
# Save suggestions to file
python -m src.ever_thinker --project state/proj_*/ > test-results/ever-thinker-suggestions.txt
```

**Evaluate suggestion quality:**
- Count total suggestions
- Count actionable suggestions (realistic to implement)
- Count novel suggestions (not obvious)
- Count valuable suggestions (you'd actually implement)

**No formal checkpoint - qualitative assessment only**

---

## Phase 6: Results Analysis (30 minutes)

### Step 6.1: Collect All Checkpoint Results

```bash
# Terminal 3 (Checkpoints)
cd /home/thh3/personal/moderator/docs/testing/test-results

# View all checkpoint results
cat ../checkpoint-1-results.txt
cat ../checkpoint-2-results.txt
cat ../checkpoint-3-results.txt
cat ../checkpoint-4-results.txt
cat ../checkpoint-5-results.txt
```

### Step 6.2: Generate Summary Report

```bash
# Create summary CSV
cat > checkpoint-summary.csv << EOF
Checkpoint,Score,Max,Status
CP1 Problem Understanding,$(grep 'Score:' ../checkpoint-1-results.txt | awk '{print $2}'),20,$(grep 'Status:' ../checkpoint-1-results.txt | awk '{print $2}')
CP2 Discovery,$(grep 'Score:' ../checkpoint-2-results.txt | awk '{print $2}'),100,$(grep 'Status:' ../checkpoint-2-results.txt | awk '{print $2}')
CP3 Architecture,$(grep 'Score:' ../checkpoint-3-results.txt | awk '{print $2}'),100,$(grep 'Status:' ../checkpoint-3-results.txt | awk '{print $2}')
CP4 QA Gates,N/A,N/A,$(grep 'Status:' ../checkpoint-4-results.txt | awk '{print $2}')
CP5 Coverage,$(grep 'Coverage:' ../checkpoint-5-results.txt | awk '{print $2}'),100,$(grep 'Status:' ../checkpoint-5-results.txt | awk '{print $2}')
EOF

# View summary
column -t -s ',' checkpoint-summary.csv
```

### Step 6.3: Calculate Overall Success Level

**Success Criteria:**

| Level | Requirements |
|-------|-------------|
| **Minimum** | 3/5 checkpoints pass at minimum level, code runs |
| **Target** | 4/5 checkpoints pass at target level, tool partially works |
| **Stretch** | 5/5 checkpoints pass at stretch level, tool fully works |

**Count passes:**
```bash
# Count how many passed
grep -c "✅ PASS\|✅ EXCELLENT" ../checkpoint-*-results.txt
```

### Step 6.4: Document Learnings

**Create learnings document:**

```bash
vim test-run-1-learnings.md
```

**Template:**
```markdown
# Test Run #1 Learnings
**Date:** 2025-01-16
**Duration:** [actual time]
**Overall Result:** [Minimum/Target/Stretch]

## Checkpoint Scores
- CP1 (Problem Understanding): [score]/20 [status]
- CP2 (Discovery): [score]/100 [status]
- CP3 (Architecture): [score]/100 [status]
- CP4 (Code Quality): [status]
- CP5 (Test Coverage): [score]% [status]

## What Worked Well
1. [Specific success]
2. [Specific success]
3. [Specific success]

## What Failed
1. [Specific failure with root cause]
2. [Specific failure with root cause]
3. [Specific failure with root cause]

## Moderator Improvements Needed
1. [Specific fix to Moderator framework]
2. [Specific fix to Moderator framework]
3. [Specific fix to Moderator framework]

## Next Iteration Plan
1. [Specific change for Run #2]
2. [Specific change for Run #2]
3. [Specific change for Run #2]

## Estimated Re-Run Date
[Date when you plan Run #2]
```

### Step 6.5: Compare to Answer Keys

**Discovery comparison:**
```bash
diff -u claude-data-schema.md test-results/discovery-output.md > test-results/discovery-diff.txt
less test-results/discovery-diff.txt
```

**Architecture comparison:**
```bash
diff -u claude-sync-architecture.md test-results/architecture.md > test-results/architecture-diff.txt
less test-results/architecture-diff.txt
```

---

## Intervention Policy

### When to Intervene (CRITICAL only)

**DO intervene if:**
- 🔴 Moderator stuck on same task >3 hours
- 🔴 Moderator about to delete important files (`rm -rf`)
- 🔴 Moderator requesting dangerous operations (`sudo rm`, system modifications)
- 🔴 Infinite loop detected (same command repeating 10+ times)
- 🔴 All SSH connections fail (network issue, not Moderator issue)

**DO NOT intervene if:**
- ❌ Moderator makes wrong architectural choice (let it fail, learn from it)
- ❌ Moderator misses a security concern (checkpoint will catch it)
- ❌ Moderator generates low-quality code (QA gates will catch it)
- ❌ Moderator doesn't ask enough questions (checkpoint will flag it)
- ❌ Moderator takes longer than expected (be patient)

### How to Intervene

**If intervention required:**

1. **Pause execution** (Ctrl+C if needed)
2. **Document the intervention** in `interventions.log`:
   ```
   [timestamp] CRITICAL: [reason]
   Action taken: [what you did]
   ```
3. **Provide minimal hint** (don't solve the problem)
4. **Resume execution**
5. **Flag this run as "assisted"** in final report

---

## Post-Test Checklist

After Phase 6 completes:

- [ ] All checkpoint results collected
- [ ] Summary CSV generated
- [ ] Learnings document written
- [ ] Answer key comparisons completed
- [ ] Top 3 Moderator improvements identified
- [ ] Next iteration plan documented
- [ ] All results backed up to `test-results/run-1/`

**Backup results:**
```bash
mkdir -p test-results/run-1
cp checkpoint-*-results.txt test-results/run-1/
cp test-run-1-learnings.md test-results/run-1/
cp checkpoint-summary.csv test-results/run-1/
```

---

## Next: Iteration 2

**Before Run #2:**
1. Fix top 3 Moderator issues identified in Run #1
2. Update instrumentation if needed (add checkpoints, improve scripts)
3. Consider if seed input needs clarification
4. Allocate time (expect 3-4 hours for Run #2)

**Goal for Run #2:**
- Improve scores by ≥20% on failed checkpoints
- Achieve "Target" success level (4/5 checkpoints at target)

---

**Document Version:** 1.0
**Created:** 2025-01-16

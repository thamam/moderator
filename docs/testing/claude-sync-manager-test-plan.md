# Claude Sync Manager - Moderator System Test Plan

**Project:** Claude Sync Manager (Multi-Machine Conversation History Sync + PR Dashboard)
**Purpose:** Real-world validation of Moderator Gear 3 & Gear 4 implementation
**Duration:** 7 days
**Test Lead:** Tomer (with Moderator guidance)
**Date Created:** 2025-01-16
**Status:** Ready for Execution

---

## Executive Summary

This test plan validates the complete Moderator system (Epics 1-7) by building a real-world tool: **Claude Sync Manager**. The tool solves an actual problem (syncing Claude Code conversations across 4 machines + unified PR dashboard) while exercising all advanced Moderator capabilities.

### Success Criteria

**Primary Goals:**
1. ✅ **Functional Tool**: Claude Sync Manager works across all 4 machines
2. ✅ **Real Value**: Tomer uses the tool daily after completion
3. ✅ **System Validation**: All 7 Moderator epics proven to work together

**Moderator Validation Goals:**
- Ever-Thinker identifies real optimization opportunities
- QA gates catch actual security/quality issues
- Monitor agent tracks real health metrics
- Learning system adapts to patterns
- Parallel execution provides measurable speedup
- Dashboard framework (Epic 7) is reusable

---

## Project Overview

### Problem Statement

Tomer works with Claude Code across 4 machines (2 Linux, 1 Mac, 1 Windows) connected via SSH on local network. Current pain points:
- Conversation history isolated per machine
- No unified view of pending PRs across repositories
- Context switching between machines loses conversation state

### Solution Architecture

**Hub-and-Spoke Design:**
- **Hub (XPS)**: Always-on central server running sync daemon, master database, PR aggregation
- **Spokes (ROG, MAC, NELLY)**: File watchers notify hub of changes, receive synced updates
- **Event-Based Sync**: Real-time synchronization triggered by file changes
- **Terminal UI**: Dashboard showing sync status, conversation history, pending PRs

### Technical Stack

| Component | Technology | Epic Validated |
|-----------|-----------|----------------|
| Sync Engine | Python + rsync over SSH | Epic 5 (Parallel Execution) |
| File Watching | watchdog library (cross-OS) | Epic 1 (Foundation) |
| Database | SQLite (centralized on XPS) | Epic 2 (Learning System) |
| PR Aggregation | GitHub CLI (`gh`) | Epic 4 (QA Integration) |
| Terminal UI | Textual + Rich | Epic 7 (Dashboard) |
| Monitoring | Monitor Agent | Epic 6 (Health Monitoring) |
| Improvement | Ever-Thinker | Epic 3 (Continuous Improvement) |

### Network Topology

```
                    XPS (Hub - 192.168.68.62)
                    Always-On Central Server
                    ┌────────────────────────┐
                    │ - Sync Daemon          │
                    │ - Master SQLite DB     │
                    │ - PR Aggregation       │
                    │ - Terminal Dashboard   │
                    └───┬────────┬────────┬──┘
                        │        │        │
            ┌───────────┴─┐  ┌──┴────┐  ┌┴──────────┐
            │ ROG (Linux) │  │ MAC   │  │ NELLY(Win)│
            │ 192.168.68  │  │.68.56 │  │ .68.60    │
            │ .65 mybox   │  │MacBook│  │ groisssman│
            └─────────────┘  └───────┘  └───────────┘
```

**SSH Configuration:**
- All machines: Passwordless SSH (keys established)
- All bidirectional connections: Working (12/12 ✓)
- Hostnames: `xps`, `rog`, `mac`, `nelly`

**Claude Code Data Locations:**
- Linux (xps, rog): `~/.config/Claude/`
- Mac: `~/Library/Application Support/Claude/`
- Windows (nelly): `%APPDATA%/Claude/`

---

## Test Strategy

### Three-Tier Validation Approach

**TIER 1: Core Functionality** (Must Pass - Blockers)
- Basic sync mechanics work
- Data integrity maintained
- PR aggregation functions
- Dashboard renders

**TIER 2: Moderator Integration** (High Value - System Validation)
- Ever-Thinker generates improvements
- QA gates catch issues
- Monitor tracks health
- Learning system adapts

**TIER 3: Advanced Features** (Nice to Have - Polish)
- Parallel execution optimization
- Edge case handling
- Real-time UI updates

### Test Execution Model

**Interactive Testing:**
- Tomer executes with agent guidance
- Agents provide context and checkpoints
- Real-time feedback and iteration
- Document learnings as we go

**Measurement Focus:**
- Functional correctness (does it work?)
- System integration (do epics cooperate?)
- Real-world value (will Tomer use it?)

---

## Phase 1: Discovery & Architecture (Day 1)

**Goal:** Understand Claude Code's data structure and create comprehensive architecture

### Tasks

#### 1.1: Discover Claude Data Locations

**Objective:** Locate and analyze Claude Code conversation files on all machines

**Steps:**
```bash
# On each machine, discover Claude data:
ssh xps "find ~/.config/Claude -type f -name '*.json*' -o -name '*.db' 2>/dev/null | head -20"
ssh rog "find ~/.config/Claude -type f -name '*.json*' -o -name '*.db' 2>/dev/null | head -20"
ssh mac "find ~/Library/Application\ Support/Claude -type f 2>/dev/null | head -20"
ssh nelly "dir C:\Users\thh3\AppData\Roaming\Claude /s /b 2>nul | findstr /i json"
```

**Acceptance Criteria:**
- [ ] Located conversation history files on all 4 machines
- [ ] Identified file format (JSON, JSONL, SQLite, etc.)
- [ ] Documented file schema and structure
- [ ] Confirmed read permissions on all machines

**Moderator Test:** Can we discover data locations programmatically?

---

#### 1.2: Analyze File Formats and Schemas

**Objective:** Reverse-engineer Claude Code's data format for safe parsing

**Steps:**
1. Extract sample conversation files from each machine
2. Analyze JSON/DB schema structure
3. Identify:
   - Conversation metadata (project, timestamp, participants)
   - Message format (user vs assistant, content structure)
   - File naming convention
   - Update/modification patterns

**Acceptance Criteria:**
- [ ] Documented complete file schema
- [ ] Identified unique conversation IDs
- [ ] Understood update/append mechanisms
- [ ] Verified cross-OS compatibility (line endings, encoding)

**Moderator Test:** Does Moderator's decomposer correctly understand the domain?

---

#### 1.3: Create Architecture Document via Moderator

**Objective:** Use Moderator to generate comprehensive system architecture

**Steps:**
1. Feed discovery findings to Moderator
2. Request architecture document generation
3. Review Winston (Architect agent) output
4. Validate against technical requirements

**Moderator Workflow:**
```bash
# Initialize Moderator with PRD
moderator "Create architecture document for Claude Sync Manager hub-and-spoke system"
```

**Acceptance Criteria:**
- [ ] Architecture document created with:
  - Component diagram (hub, spokes, sync engine, PR service)
  - Data flow diagram (event-based sync protocol)
  - Technology stack decisions with rationale
  - API contracts (SSH commands, rsync protocol)
  - Error handling strategy
  - Security considerations (SSH key management)
- [ ] Document reviewed and approved by Tomer

**Moderator Test:**
- Quality of architecture decisions
- Completeness of technical specifications
- Proper use of Epic 1 (Foundation) patterns

---

#### 1.4: Generate PRD using Moderator PM Agent

**Objective:** Create detailed Product Requirements Document through John (PM agent)

**Steps:**
1. Invoke Moderator's PM agent (John)
2. Provide problem statement and constraints
3. Generate user stories with acceptance criteria
4. Validate epic breakdown

**Moderator Workflow:**
```bash
# Engage PM agent
moderator pm --mode=interactive
# Provide: problem, network topology, machines, requirements
```

**Acceptance Criteria:**
- [ ] PRD created with:
  - User stories (sync, PR dashboard, UI)
  - Acceptance criteria per story
  - Epic breakdown (3-5 epics recommended)
  - Success metrics (functional, performance, UX)
  - Risk assessment and mitigation
- [ ] PRD approved by Tomer

**Moderator Test:**
- PM agent asks right probing questions
- Stories are clear and actionable
- Epic breakdown aligns with architecture

---

### Phase 1 Validation

**Checkpoint Questions:**
1. Do we fully understand Claude Code's data format?
2. Is the architecture sound for the hub-and-spoke model?
3. Are the requirements clear and complete?
4. Did Moderator add value or just generate boilerplate?

**Phase 1 Success Criteria:**
- [ ] All discovery tasks completed
- [ ] Architecture document exists and is sound
- [ ] PRD exists with clear user stories
- [ ] Moderator demonstrated intelligent decomposition
- [ ] Ready to proceed to implementation

---

## Phase 2: MVP Implementation - Sync Engine (Days 2-3)

**Goal:** Build core synchronization engine with event-based monitoring

### Epic 2.1: Hub Service on XPS

**Story:** As the system, I need a persistent hub service on XPS that monitors spoke machines for changes.

**Implementation Tasks:**

#### Task 2.1.1: Hub Service Daemon
```python
# File: src/sync_hub/daemon.py
class ClaudeSyncHub:
    """Central hub service running on XPS (always-on)."""

    machines = {
        'rog': {'ip': '192.168.68.65', 'hostname': 'mybox', 'os': 'linux'},
        'mac': {'ip': '192.168.68.56', 'hostname': 'Tomers-MacBook-Pro', 'os': 'mac'},
        'nelly': {'ip': '192.168.68.60', 'hostname': 'groisssman', 'os': 'windows'}
    }

    def start_daemon(self):
        """Start persistent background service."""
        # TODO: Implement

    def watch_spoke(self, machine_name):
        """Monitor spoke machine for file changes via SSH."""
        # TODO: Implement with watchdog or inotify

    def handle_change_event(self, machine, filepath):
        """React to file change notification."""
        # TODO: Trigger sync
```

**Acceptance Criteria:**
- [ ] Daemon starts on XPS boot (systemd service or similar)
- [ ] Monitors all 3 spoke machines concurrently
- [ ] Logs events to structured log file
- [ ] Graceful shutdown on SIGTERM
- [ ] Restarts automatically on crash

**Moderator Test:**
- Epic 5 (Parallel Execution): Does parallel monitoring of 3 machines work?
- Epic 6 (Monitoring): Does Monitor agent track hub service health?

---

#### Task 2.1.2: Remote File Watching

**Challenge:** Detect file changes on remote machines via SSH

**Implementation Options:**

**Option A: Polling** (Simple, cross-OS compatible)
```bash
# Every 10 seconds, check for new/modified files
ssh rog "find ~/.config/Claude -type f -newer /tmp/last_sync.timestamp"
```

**Option B: Remote inotify** (Linux only, event-driven)
```bash
# SSH tunnel with inotifywait
ssh rog "inotifywait -m -r ~/.config/Claude -e modify,create"
```

**Option C: Hybrid** (Recommended)
- Linux spokes: inotify via SSH
- Mac spoke: FSEvents via SSH
- Windows spoke: Polling (10s interval)

**Acceptance Criteria:**
- [ ] Detects new conversation files within 10 seconds
- [ ] Detects modifications to existing files
- [ ] Handles SSH connection drops gracefully
- [ ] No false positives (temp files, locks, etc.)

**Moderator Test:**
- Epic 4 (QA): Does bandit flag security issues (SSH command injection)?
- Epic 2 (Learning): Does system learn optimal polling intervals?

---

### Epic 2.2: Spoke Agents (Cross-OS)

**Story:** As a spoke machine, I need a lightweight agent that reports changes to the hub.

**Implementation:** Optional - can use SSH-based remote monitoring from hub instead

**Decision Point:**
- **Deploy agents?** More complex but event-driven (lower latency)
- **Hub polling?** Simpler but 10s sync delay

**Recommendation:** Start with hub-only polling (simpler), add spoke agents in improvement cycle if Ever-Thinker suggests it.

---

### Epic 2.3: Sync Protocol (rsync over SSH)

**Story:** As the hub, I need to sync conversation files bidirectionally with data integrity guarantees.

#### Task 2.3.1: One-Way Sync (Spoke → Hub)

```python
def sync_from_spoke(self, machine, claude_path):
    """Pull latest conversations from spoke to hub."""
    hub_path = f"/var/lib/claude-sync/{machine}/"

    # rsync over SSH with conflict detection
    cmd = [
        'rsync', '-avz', '--checksum',
        f'{machine}:{claude_path}',
        hub_path
    ]

    # TODO: Error handling, conflict detection
```

**Acceptance Criteria:**
- [ ] Syncs all conversation files from spoke to hub
- [ ] Preserves file metadata (timestamps, permissions)
- [ ] Handles large files (>10MB) without corruption
- [ ] Detects conflicts (file modified on multiple machines)
- [ ] Logs sync statistics (files transferred, bytes, duration)

---

#### Task 2.3.2: Bidirectional Sync (Hub → Spokes)

```python
def sync_to_spokes(self, source_machine, target_machines):
    """Push updated conversations from hub to all other spokes."""
    source_path = f"/var/lib/claude-sync/{source_machine}/"

    for target in target_machines:
        if target == source_machine:
            continue

        target_claude_path = self.machines[target]['claude_path']

        # Push to target
        cmd = [
            'rsync', '-avz', '--checksum',
            source_path,
            f'{target}:{target_claude_path}'
        ]

        # TODO: Conflict resolution, rollback on failure
```

**Acceptance Criteria:**
- [ ] Updates propagate to all machines within 30 seconds
- [ ] No data loss during bidirectional sync
- [ ] Conflict resolution works (last-write-wins or manual merge)
- [ ] Failed syncs don't corrupt existing data

**Moderator Test:**
- Epic 5 (Parallel Execution): Sync to 3 spokes simultaneously
- Epic 6 (Monitor): Track sync latency and failure rate

---

### Epic 2.4: Conflict Resolution

**Story:** When the same conversation is modified on multiple machines, resolve conflicts intelligently.

**Conflict Detection:**
```python
def detect_conflict(self, filepath):
    """Check if file has been modified on multiple machines since last sync."""
    hub_version = self.get_file_hash(filepath, machine='hub')

    conflicts = []
    for machine in self.machines:
        spoke_version = self.get_file_hash(filepath, machine=machine)
        spoke_mtime = self.get_mtime(filepath, machine=machine)

        if spoke_version != hub_version and spoke_mtime > last_sync_time:
            conflicts.append(machine)

    return len(conflicts) > 1  # Conflict if 2+ machines modified
```

**Resolution Strategies:**

**Strategy 1: Last-Write-Wins** (Simple, may lose data)
- Keep version with most recent timestamp
- Log discarded version for manual recovery

**Strategy 2: Append-Only Merge** (Safe for conversation logs)
- Merge messages from both versions chronologically
- Mark conflict in metadata

**Strategy 3: Manual Resolution** (Safest)
- Alert user via dashboard
- Present both versions side-by-side
- User chooses which to keep

**Acceptance Criteria:**
- [ ] Conflicts detected reliably (100% detection rate)
- [ ] Resolution strategy configurable (CLI flag or config)
- [ ] No silent data loss
- [ ] Conflict history logged for audit

**Moderator Test:**
- Epic 3 (Ever-Thinker): Does it suggest better conflict strategies?
- Epic 4 (QA): Does code handle edge cases (empty files, binary data)?

---

### Phase 2 Validation

**Real-World Test Scenario:**
1. Create conversation on ROG
2. Verify sync to XPS within 10 seconds
3. Verify propagation to MAC and NELLY within 30 seconds
4. Modify same conversation on MAC and NELLY simultaneously
5. Verify conflict detected and resolved correctly

**Phase 2 Success Criteria:**
- [ ] Basic sync loop works end-to-end
- [ ] All 4 machines stay in sync
- [ ] No data corruption or loss
- [ ] Moderator's parallel execution provides speedup (measure!)
- [ ] QA gates caught at least 1 real issue

---

## Phase 3: PR Aggregation (Day 4)

**Goal:** Unified dashboard of pending PRs across all repositories

### Epic 3.1: GitHub API Integration

**Story:** As Tomer, I want to see all my pending PRs in one place across all repositories.

#### Task 3.1.1: GitHub CLI Setup

**Prerequisites:**
- GitHub CLI (`gh`) installed on XPS
- Authenticated: `gh auth login`

**Implementation:**
```python
import subprocess
import json

class PRDashboard:
    """Aggregate PRs across all repositories."""

    def fetch_all_prs(self):
        """Fetch PRs from all accessible repositories."""
        # gh pr list --json <fields> --limit 100
        cmd = [
            'gh', 'pr', 'list',
            '--json', 'number,title,state,repository,updatedAt,author',
            '--limit', '100'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        prs = json.loads(result.stdout)
        return prs

    def group_by_repo(self, prs):
        """Group PRs by repository for dashboard display."""
        by_repo = {}
        for pr in prs:
            repo = pr['repository']['name']
            if repo not in by_repo:
                by_repo[repo] = []
            by_repo[repo].append(pr)
        return by_repo
```

**Acceptance Criteria:**
- [ ] Fetches PRs from all accessible repositories
- [ ] Includes PR metadata: number, title, state, updated time, author
- [ ] Handles API rate limits gracefully
- [ ] Groups PRs by repository
- [ ] Filters by state (open, draft, review, merged)

---

#### Task 3.1.2: Multi-Repo PR Tracking

**Challenge:** Track PRs across Tomer's multiple repositories

**Discovery:**
```bash
# List all repositories Tomer has access to
gh repo list --limit 100 --json name,owner

# For each repo, get PR count
gh pr list --repo <owner/repo> --state open --json number
```

**Implementation:**
```python
def discover_repositories(self):
    """Find all repositories user has access to."""
    cmd = ['gh', 'repo', 'list', '--limit', '100', '--json', 'nameWithOwner']
    result = subprocess.run(cmd, capture_output=True, text=True)
    repos = json.loads(result.stdout)
    return [r['nameWithOwner'] for r in repos]

def fetch_prs_for_repo(self, repo):
    """Fetch PRs for specific repository."""
    cmd = [
        'gh', 'pr', 'list',
        '--repo', repo,
        '--state', 'open',
        '--json', 'number,title,updatedAt,isDraft'
    ]
    # TODO: Error handling (repo doesn't exist, no access, etc.)
```

**Acceptance Criteria:**
- [ ] Discovers all accessible repositories
- [ ] Fetches PRs from each repository
- [ ] Handles repositories with no PRs
- [ ] Handles private repositories (authentication)
- [ ] Caches results to avoid rate limits (refresh every 5 minutes)

**Moderator Test:**
- Epic 6 (Monitor): Track GitHub API health (rate limits, failures)
- Epic 2 (Learning): Learn which repos have most active PRs

---

### Epic 3.2: PR Status Tracking

**Story:** As Tomer, I want to see PR status at a glance (ready for review, changes requested, approved, merged).

**GitHub PR States:**
- `OPEN` - Active PR
- `DRAFT` - Work in progress
- `MERGED` - Completed
- `CLOSED` - Abandoned

**Review Status:**
- `APPROVED` - Ready to merge
- `CHANGES_REQUESTED` - Needs work
- `REVIEW_REQUIRED` - Awaiting review

**Implementation:**
```python
def get_pr_status(self, repo, pr_number):
    """Get detailed PR status including review state."""
    cmd = [
        'gh', 'pr', 'view', str(pr_number),
        '--repo', repo,
        '--json', 'state,isDraft,reviewDecision,statusCheckRollup'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    pr_data = json.loads(result.stdout)

    # Determine display status
    if pr_data['state'] == 'MERGED':
        return 'merged', 'green'
    elif pr_data['isDraft']:
        return 'draft', 'gray'
    elif pr_data['reviewDecision'] == 'APPROVED':
        return 'approved', 'green'
    elif pr_data['reviewDecision'] == 'CHANGES_REQUESTED':
        return 'changes requested', 'red'
    else:
        return 'awaiting review', 'yellow'
```

**Acceptance Criteria:**
- [ ] Displays accurate PR state
- [ ] Shows review status (approved/changes/pending)
- [ ] Color-coded badges (green/yellow/red)
- [ ] Indicates CI/CD status (checks passing/failing)
- [ ] Shows last update timestamp

---

### Phase 3 Validation

**Real-World Test:**
1. Create test PR in one of Tomer's repositories
2. Verify it appears in dashboard within 5 minutes
3. Request changes on PR
4. Verify status updates in dashboard
5. Merge PR
6. Verify dashboard reflects merged state

**Phase 3 Success Criteria:**
- [ ] PR aggregation works across all repositories
- [ ] Status tracking is accurate
- [ ] Dashboard updates within reasonable time (5 min)
- [ ] Monitor agent tracks GitHub API health

---

## Phase 4: Terminal UI Dashboard (Day 5)

**Goal:** Build interactive terminal dashboard reusing Epic 7 framework

### Epic 4.1: Reuse Epic 7 Dashboard Framework

**Story:** As a developer, I want to reuse the BasePanel pattern from Epic 7 to build the sync dashboard quickly.

**Epic 7 Assets to Reuse:**
- `src/dashboard/panels/base_panel.py` - BasePanel abstract class
- `src/dashboard/monitor_dashboard.py` - MonitorDashboardApp framework
- Textual + Rich styling patterns
- Auto-refresh mechanism (3-second interval)
- Keyboard shortcuts (Tab, Enter, Q, ?)

**Implementation:**
```python
# File: src/claude_sync/dashboard/sync_dashboard.py
from src.dashboard.monitor_dashboard import MonitorDashboardApp
from src.dashboard.panels.base_panel import BasePanel

class ClaudeSyncDashboard(MonitorDashboardApp):
    """Main dashboard for Claude Sync Manager."""

    def __init__(self):
        super().__init__(
            title="Claude Sync Manager",
            subtitle="Multi-Machine Conversation Sync + PR Dashboard"
        )

        # Override panels
        self.panels = {
            'sync_status': SyncStatusPanel(),
            'conversations': ConversationHistoryPanel(),
            'prs': PRDashboardPanel(),
            'health': SystemHealthPanel()
        }
```

**Acceptance Criteria:**
- [ ] Dashboard launches without errors
- [ ] All 4 panels visible
- [ ] Auto-refresh works (3-second interval)
- [ ] Keyboard shortcuts functional (Tab, Q, ?)
- [ ] Help screen displays

**Moderator Test:**
- **Code Reuse Metric**: What % of Epic 7 code was reused vs rewritten?
- **Quality**: Does reused framework work without modification?

---

### Epic 4.2: Sync Status Panel

**Story:** As Tomer, I want to see sync status for all 4 machines at a glance.

**Panel Layout:**
```
┌─ Sync Status ────────────────────────────────────────┐
│ Overall: ✅ 4/4 Machines Synced                      │
│ Last Sync: 2025-01-16 14:32:15                       │
│                                                       │
│ Machine    Status  Last Sync        Files  Conflicts │
│ ─────────────────────────────────────────────────────│
│ 🖥️  XPS     🟢 Hub  (always current)  1,234  0       │
│ 🐧 ROG     🟢 OK   14:32:10 (5s ago) 1,234  0       │
│ 🍎 MAC     🟢 OK   14:32:12 (3s ago) 1,234  0       │
│ 🪟 NELLY   🟡 SLOW 14:31:45 (30s)    1,233  1       │
│                                                       │
│ Sync Rate: 3.2 MB/s | Avg Latency: 8.4s             │
└───────────────────────────────────────────────────────┘
```

**Implementation:**
```python
from src.dashboard.panels.base_panel import BasePanel
from textual.reactive import reactive

class SyncStatusPanel(BasePanel):
    """Display sync status for all machines."""

    machine_statuses: dict = reactive({})
    last_sync_time: str = reactive("")

    async def refresh_data(self):
        """Fetch latest sync status from hub service."""
        # Query hub service for machine statuses
        self.machine_statuses = self.hub.get_machine_statuses()
        self.last_sync_time = self.hub.get_last_sync_time()

    def render_content(self) -> str:
        """Render sync status table."""
        # TODO: Render table with machine statuses
```

**Acceptance Criteria:**
- [ ] Shows all 4 machines with status icons (🟢/🟡/🔴)
- [ ] Displays last sync timestamp (relative: "5s ago")
- [ ] Shows file counts per machine
- [ ] Highlights conflicts (if any)
- [ ] Shows sync throughput (MB/s) and latency

---

### Epic 4.3: Conversation History Panel

**Story:** As Tomer, I want to browse recent conversations grouped by project.

**Panel Layout:**
```
┌─ Recent Conversations ──────────────────────────────┐
│ moderator (5 sessions)                              │
│   └─ 2025-01-16 14:30 | Epic 7 Testing (ROG)      │
│   └─ 2025-01-16 12:15 | Dashboard Polish (MAC)    │
│   └─ 2025-01-15 18:45 | Story 7.5 Review (XPS)    │
│                                                     │
│ my-app (3 sessions)                                 │
│   └─ 2025-01-16 10:22 | API Refactor (NELLY)      │
│   └─ 2025-01-14 16:30 | Auth Bug Fix (ROG)        │
│                                                     │
│ Press Enter to view full conversation history      │
└─────────────────────────────────────────────────────┘
```

**Implementation:**
```python
class ConversationHistoryPanel(BasePanel):
    """Display recent conversations grouped by project."""

    conversations: list = reactive([])

    async def refresh_data(self):
        """Load recent conversations from hub database."""
        # Query SQLite DB on hub
        self.conversations = self.hub.get_recent_conversations(limit=20)

    def render_content(self) -> str:
        """Render conversation list grouped by project."""
        # Group by project
        by_project = {}
        for conv in self.conversations:
            project = conv['project']
            if project not in by_project:
                by_project[project] = []
            by_project[project].append(conv)

        # Render grouped list
        # TODO: Format with timestamps, machine indicators
```

**Acceptance Criteria:**
- [ ] Shows last 20 conversations
- [ ] Grouped by project/repository
- [ ] Displays timestamp and machine origin
- [ ] Expandable to show full history
- [ ] Clickable to open conversation (optional - v2)

---

### Epic 4.4: PR Dashboard Panel

**Story:** As Tomer, I want to see all pending PRs grouped by repository with status indicators.

**Panel Layout:**
```
┌─ Pull Requests ─────────────────────────────────────┐
│ 🔴 3 Critical  🟡 5 Awaiting Review  🟢 2 Approved  │
│                                                     │
│ moderator (2 PRs)                                   │
│   #42 🟢 Story 7.5 Implementation (approved)       │
│   #41 🟡 Epic 7 Planning Docs (review)             │
│                                                     │
│ my-app (3 PRs)                                      │
│   #15 🔴 Hotfix: Auth Crash (changes requested)    │
│   #14 🟡 Feature: Export (awaiting review)         │
│   #12 🟢 Refactor: API Client (approved)           │
│                                                     │
│ Press Enter to expand PR details                   │
└─────────────────────────────────────────────────────┘
```

**Implementation:**
```python
class PRDashboardPanel(BasePanel):
    """Display pending PRs grouped by repository."""

    prs: list = reactive([])
    pr_summary: dict = reactive({})

    async def refresh_data(self):
        """Fetch latest PRs from GitHub."""
        self.prs = self.pr_service.fetch_all_prs()
        self.pr_summary = self.pr_service.get_summary()

    def render_content(self) -> str:
        """Render PR list with status badges."""
        # TODO: Group by repo, color-code by status
```

**Acceptance Criteria:**
- [ ] Shows all open PRs across repositories
- [ ] Grouped by repository
- [ ] Status badges color-coded (🟢/🟡/🔴)
- [ ] Summary bar (counts by status)
- [ ] Expandable for PR details (author, checks, reviews)

---

### Phase 4 Validation

**Dashboard Manual Verification:**
1. Launch dashboard: `python -m src.claude_sync.dashboard.sync_dashboard`
2. Verify all 4 panels render correctly
3. Check auto-refresh (3-second interval)
4. Test keyboard shortcuts (Tab, Q, ?)
5. Create conversation on ROG → Verify appears in dashboard within 10s
6. Create PR on GitHub → Verify appears in dashboard within 5 min

**Phase 4 Success Criteria:**
- [ ] Dashboard production-ready (no crashes)
- [ ] All panels functional and updating
- [ ] Reused Epic 7 code successfully (measure reuse %)
- [ ] UX is smooth and responsive

---

## Phase 5: Improvement Cycle (Day 6)

**Goal:** Validate Ever-Thinker, QA integration, and Learning system with real-world improvements

### Epic 5.1: Trigger Ever-Thinker

**Story:** As a completed project, I want the Ever-Thinker to analyze my code and suggest improvements.

**Implementation:**
```bash
# After Phase 4 completion, trigger improvement cycle
moderator improve --project=claude-sync-manager --perspectives=all
```

**Ever-Thinker Perspectives (Epic 3):**
1. **Performance Analyzer**: Identify sync bottlenecks, caching opportunities
2. **Code Quality Analyzer**: Find code smells, duplication, complexity
3. **Testing Analyzer**: Suggest missing test cases, edge cases
4. **Documentation Analyzer**: Identify undocumented functions, outdated docs
5. **UX Analyzer**: Suggest dashboard improvements, keyboard shortcuts
6. **Architecture Analyzer**: Identify coupling issues, refactoring opportunities

**Expected Improvements:**
- Caching for GitHub API calls (rate limit optimization)
- Parallel rsync for faster multi-machine sync
- Better conflict resolution UX
- Additional test coverage for edge cases
- Performance metrics collection

**Acceptance Criteria:**
- [ ] Ever-Thinker generates 5-10 improvement suggestions
- [ ] Suggestions are concrete and actionable (not vague)
- [ ] At least 3 suggestions are valuable (Tomer agrees to implement)
- [ ] Suggestions create PRs for review

---

### Epic 5.2: Validate QA Integration

**Story:** As a quality-conscious system, I want QA tools to catch issues before merge.

**QA Tools (Epic 4):**
- **Pylint**: Code quality, style violations
- **Flake8**: PEP 8 compliance, complexity
- **Bandit**: Security vulnerabilities (hardcoded secrets, command injection)

**Test Scenarios:**

#### Scenario 1: Security Issue Detection
```python
# Intentionally introduce security flaw
def sync_file(machine, filepath):
    # SECURITY FLAW: Command injection risk
    cmd = f"rsync {filepath} {machine}:/backup/"  # ⚠️ No sanitization
    os.system(cmd)  # ⚠️ Dangerous!
```

**Expected:** Bandit should flag this as HIGH severity command injection risk

#### Scenario 2: Code Quality Issue
```python
# Intentionally write complex code
def process_sync(m, f, s, t, c, o):  # ⚠️ Unclear variable names
    if c:
        if t == 'l':
            if o:
                # 10 levels of nesting...  ⚠️ High cyclomatic complexity
```

**Expected:** Flake8/Pylint should flag high complexity and unclear names

#### Scenario 3: QA Gate Enforcement
- Commit code with intentional issues
- Run Moderator's PR review workflow
- Verify QA gates **block merge** with score < 80

**Acceptance Criteria:**
- [ ] Bandit catches at least 1 real security issue
- [ ] Pylint/Flake8 identify code quality problems
- [ ] QA gates prevent merge of failing code
- [ ] QA scores displayed in dashboard/PR comments

**Moderator Test:**
- **QA Integration Works**: Tools run automatically in PR workflow
- **Gate Enforcement**: Failed QA blocks merge (score < 80)
- **Useful Feedback**: QA findings help improve code quality

---

### Epic 5.3: Validate Learning System

**Story:** As a learning system, I want to remember patterns and adapt behavior over time.

**Learning Database (Epic 2):**
- SQLite database: `/var/lib/moderator/learning.db`
- Tables: `patterns`, `outcomes`, `improvements`

**Test Scenarios:**

#### Scenario 1: Pattern Recognition
```sql
-- After 5 successful syncs, system should learn:
SELECT * FROM patterns WHERE pattern_type = 'sync_timing';
-- Expected: "ROG syncs fastest between 8am-10am"
-- Expected: "NELLY syncs slowest due to Windows overhead"
```

#### Scenario 2: Improvement Tracking
```sql
-- After accepting Ever-Thinker suggestion:
SELECT * FROM improvements WHERE status = 'accepted';
-- Expected: Suggestion text, outcome, impact measurement
```

#### Scenario 3: Adaptive Behavior
- **Before Learning**: Sync all machines sequentially (slow)
- **After Learning**: Sync ROG + MAC in parallel, NELLY separately (faster)
- **Validation**: System adapts without manual configuration

**Acceptance Criteria:**
- [ ] Learning database populates during operation
- [ ] Patterns identified after 5+ executions
- [ ] System adapts behavior based on learned patterns
- [ ] Improvements tracked with outcomes (accepted/rejected/impact)

**Moderator Test:**
- **Learning Works**: Database grows with operation
- **Patterns Emerge**: System identifies recurring behaviors
- **Adaptation**: System changes strategy based on learning

---

### Phase 5 Validation

**Improvement Cycle Scorecard:**

| Aspect | Metric | Target | Actual |
|--------|--------|--------|--------|
| Ever-Thinker Suggestions | Count | 5-10 | __ |
| Valuable Suggestions | % Accepted | >30% | __% |
| QA Issues Found | Count | >3 | __ |
| QA Gate Blocks | Success | 100% | __% |
| Patterns Learned | Count | >5 | __ |
| Adaptive Changes | Count | >1 | __ |

**Phase 5 Success Criteria:**
- [ ] Ever-Thinker provided real value (Tomer accepted ≥3 suggestions)
- [ ] QA tools caught real issues (not just style nitpicks)
- [ ] Learning system demonstrated adaptation
- [ ] Improvement cycle completed end-to-end

---

## Phase 6: Real-World Validation (Day 7)

**Goal:** Deploy to production (XPS) and validate with actual daily usage

### Deployment Checklist

**XPS Setup:**
```bash
# 1. Clone repository to XPS
ssh xps
cd /opt
git clone <claude-sync-manager-repo>
cd claude-sync-manager

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure systemd service
sudo cp scripts/claude-sync-hub.service /etc/systemd/system/
sudo systemctl enable claude-sync-hub
sudo systemctl start claude-sync-hub

# 4. Verify service running
sudo systemctl status claude-sync-hub
journalctl -u claude-sync-hub -f

# 5. Launch dashboard
python -m src.claude_sync.dashboard.sync_dashboard
```

**Acceptance Criteria:**
- [ ] Hub service runs on XPS boot
- [ ] Dashboard launches without errors
- [ ] Sync works across all 4 machines
- [ ] PR aggregation functional

---

### Real-World Usage Test (7 Days)

**Daily Usage Checklist:**

**Day 7 (Deployment):**
- [ ] Create conversation on ROG → Verify syncs to XPS
- [ ] Continue conversation on MAC → Verify history accessible
- [ ] Check PR dashboard shows all pending PRs
- [ ] No crashes or errors in logs

**Day 8-10 (Active Use):**
- [ ] Use Claude Code on different machines daily
- [ ] Monitor sync latency (should be <10s)
- [ ] Verify no data loss or corruption
- [ ] Check for conflicts (if editing same project on 2 machines)

**Day 11-13 (Improvement Tracking):**
- [ ] Review Ever-Thinker suggestions (if any generated)
- [ ] Check learning database for patterns
- [ ] Monitor system health via dashboard
- [ ] Collect performance metrics

**Day 14 (Final Validation):**
- [ ] Retrospective: Did the tool solve the problem?
- [ ] Would Tomer use this daily going forward?
- [ ] What's missing or needs improvement?

---

### Success Metrics Collection

**Functional Metrics:**
- Sync success rate: __% (target: >99%)
- Avg sync latency: __s (target: <10s)
- PR fetch success rate: __% (target: >95%)
- Uptime: __% (target: >99.9%)

**System Validation Metrics:**
- Ever-Thinker suggestions implemented: __ / __ (target: >30%)
- QA issues found: __ (target: >3)
- Learning patterns discovered: __ (target: >5)
- Parallel execution speedup: __x (target: >1.5x)

**User Value Metrics:**
- Daily active use: Yes / No
- Problem solved: Yes / No
- Would recommend: Yes / No

---

### Phase 6 Success Criteria

- [ ] Tool deployed and running on XPS
- [ ] 7 days of successful real-world usage
- [ ] No critical bugs or data loss
- [ ] Tomer commits to daily use
- [ ] All Moderator system components validated

---

## Final Retrospective

**Retrospective Questions:**

### Moderator System Performance

1. **Decomposition Quality**
   - Did Moderator correctly understand the project requirements?
   - Were generated user stories clear and actionable?
   - Did epic breakdown make sense?

2. **Implementation Quality**
   - Did generated code follow best practices?
   - Were there major bugs or design flaws?
   - How much manual intervention was needed?

3. **QA Integration**
   - Did QA tools catch real issues (not just noise)?
   - Were QA scores meaningful?
   - Did gates prevent bad code from merging?

4. **Ever-Thinker Value**
   - Were improvement suggestions useful?
   - Did suggestions demonstrate deep understanding?
   - Would you accept Ever-Thinker PRs in the future?

5. **Learning System**
   - Did system adapt behavior over time?
   - Were learned patterns meaningful?
   - Did learning improve performance/quality?

6. **Monitoring & Health**
   - Did Monitor agent catch real issues?
   - Were alerts actionable?
   - Was dashboard useful for debugging?

7. **Parallel Execution**
   - Did parallelization provide real speedup?
   - Were there race conditions or conflicts?
   - Was complexity justified by performance gain?

---

### Tool Performance

1. **Functional Success**
   - Does the tool solve your conversation sync problem?
   - Is the PR dashboard useful?
   - Would you use this daily?

2. **Reliability**
   - Any data loss or corruption?
   - Uptime acceptable?
   - How often did you need to intervene?

3. **Performance**
   - Is sync fast enough (<10s)?
   - Is dashboard responsive?
   - Any bottlenecks or slowness?

4. **Usability**
   - Is the terminal UI intuitive?
   - Are keyboard shortcuts useful?
   - What features are missing?

---

### Lessons Learned

**What Went Well:**
- (To be filled during retrospective)

**What Needs Improvement:**
- (To be filled during retrospective)

**Moderator System Enhancements:**
- (Specific improvements to Moderator based on learnings)

**Tool Enhancements:**
- (Features to add to Claude Sync Manager)

---

## Appendices

### Appendix A: Machine Configuration

| Machine | OS | IP | Hostname | SSH Key | Claude Path |
|---------|----|----|----------|---------|-------------|
| XPS (Hub) | Linux | 192.168.68.62 | xps-XPS-8940 | ~/.ssh/id_rsa | ~/.config/Claude/ |
| ROG | Linux | 192.168.68.65 | mybox | ~/.ssh/id_rsa | ~/.config/Claude/ |
| MAC | macOS | 192.168.68.56 | Tomers-MacBook-Pro | ~/.ssh/id_rsa | ~/Library/Application Support/Claude/ |
| NELLY | Windows 11 | 192.168.68.60 | groisssman | ~/.ssh/id_rsa | %APPDATA%/Claude/ |

**SSH Test Commands:**
```bash
# From any machine, test bidirectional connectivity:
ssh xps "hostname && echo 'XPS reachable'"
ssh rog "hostname && echo 'ROG reachable'"
ssh mac "hostname && echo 'MAC reachable'"
ssh nelly "hostname && echo 'NELLY reachable'"
```

---

### Appendix B: Moderator Epic Reference

| Epic | Name | Key Components | Validation Focus |
|------|------|----------------|------------------|
| 1 | Foundation & Infrastructure | Agent lifecycle, message bus, config | Does orchestration work? |
| 2 | Learning System | SQLite DB, pattern recognition | Does system learn and adapt? |
| 3 | Ever-Thinker | Background analyzer, multi-perspective | Are suggestions valuable? |
| 4 | QA Integration | Pylint, flake8, bandit | Do gates catch real issues? |
| 5 | Parallel Execution | ThreadPool, backend routing | Does parallelism speed up? |
| 6 | Health Monitoring | Metrics, anomaly detection, alerts | Does monitoring catch failures? |
| 7 | Terminal UI Dashboard | Textual framework, 4 panels | Is framework reusable? |

---

### Appendix C: Reference Documentation

**Moderator Documentation:**
- [CLAUDE.md](/home/thh3/personal/moderator/CLAUDE.md)
- [Sprint Status](/home/thh3/personal/moderator/bmad-docs/sprint-status.yaml)
- [Epic 7 Stories](/home/thh3/personal/moderator/bmad-docs/stories/7-*.md)

**SSH Network Documentation:**
- [SSH Setup Guide](/home/thh3/Documents/ssh_network_setup.md)

**External References:**
- [Textual Framework Docs](https://textual.textualize.io/)
- [GitHub CLI Docs](https://cli.github.com/manual/)
- [rsync Documentation](https://rsync.samba.org/)

---

### Appendix D: Test Execution Log

**Phase Completion Tracker:**

| Phase | Start Date | End Date | Status | Notes |
|-------|-----------|----------|--------|-------|
| Phase 1: Discovery | | | ⏸️ Pending | |
| Phase 2: Sync Engine | | | ⏸️ Pending | |
| Phase 3: PR Aggregation | | | ⏸️ Pending | |
| Phase 4: Terminal UI | | | ⏸️ Pending | |
| Phase 5: Improvement | | | ⏸️ Pending | |
| Phase 6: Real-World | | | ⏸️ Pending | |

**Issues Log:**

| # | Phase | Issue Description | Severity | Status | Resolution |
|---|-------|------------------|----------|--------|------------|
| 1 | | | | | |

---

**Document Version:** 1.0
**Last Updated:** 2025-01-16
**Next Review:** After Phase 1 completion

---

## Quick Start

**To begin testing, execute Phase 1:**

```bash
# 1. Discover Claude data locations
ssh xps "find ~/.config/Claude -type f 2>/dev/null | head -20"
ssh rog "find ~/.config/Claude -type f 2>/dev/null | head -20"
ssh mac "find ~/Library/Application\ Support/Claude -type f 2>/dev/null | head -20"
ssh nelly "dir C:\Users\thh3\AppData\Roaming\Claude /s /b 2>nul | findstr json"

# 2. Review findings and proceed to architecture creation
```

**Ready? Let's build this! 🚀**

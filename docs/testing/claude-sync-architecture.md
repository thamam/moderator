# Claude Sync Manager - System Architecture

**Project:** Claude Sync Manager (Multi-Machine Conversation History Sync + PR Dashboard)
**Architecture Version:** 1.0
**Created:** 2025-01-16 (Phase 1, Task 1.3)
**Architects:** Winston (Lead), with Team Input

---

## 1. Executive Summary

### 1.1 System Purpose

Claude Sync Manager is a hub-and-spoke distributed system that synchronizes Claude Code CLI data across 4 machines (2 Linux, 1 macOS, 1 Windows) with real-time event-based synchronization and unified PR dashboard.

### 1.2 Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Hub-and-Spoke Topology** | XPS always-on → central coordinator, simplifies conflict resolution |
| **Event-Based Sync** | <10s latency requirement → file watching triggers immediate sync |
| **rsync over SSH** | Battle-tested, efficient incremental sync, works cross-platform |
| **SQLite Central Index** | Lightweight, file-based, perfect for tracking sync state on hub |
| **Textual Framework UI** | Reuse Epic 7 dashboard components (proven working) |

### 1.3 Non-Functional Requirements

- **Sync Latency**: <10 seconds from file change to propagation
- **Data Integrity**: Zero data loss, conflict detection mandatory
- **Availability**: Hub service 99.9% uptime (restart on crash)
- **Security**: SSH key authentication, credentials excluded from sync
- **Cross-Platform**: Linux, macOS, Windows support

---

## 2. System Context

### 2.1 Network Topology

```
                     Local Network (192.168.68.0/22)
                              WLAN
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
        │ XPS (Hub)    │ │ ROG        │ │ MAC        │
        │ .68.62       │ │ .68.65     │ │ .68.56     │
        │ Always-On    │ │ Linux      │ │ macOS      │
        │ 684MB data   │ │ 132MB data │ │ 7.6MB data │
        └──────────────┘ └────────────┘ └────────────┘
                │
                │
        ┌───────▼──────┐
        │ NELLY        │
        │ .68.60       │
        │ Windows 11   │
        │ 36KB data    │
        └──────────────┘
```

**SSH Connectivity Matrix:**
- All machines: Passwordless SSH (ed25519 keys)
- All bidirectional paths: Verified working (12/12)
- Hostnames configured: `xps`, `rog`, `mac`, `nelly`

### 2.2 Data Distribution

**Total Dataset: ~824 MB across 4 machines**

| Machine | Role | Data Size | Active Projects | User |
|---------|------|-----------|-----------------|------|
| XPS | Hub + Spoke | 684 MB | Extensive (MCP configs) | thh3 |
| ROG | Spoke | 132 MB | 26 projects | thh3 |
| MAC | Spoke | 7.6 MB | 8 projects | tomerhamam |
| NELLY | Spoke | 36 KB | Minimal | nelly |

---

## 3. Component Architecture

### 3.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                    XPS (Hub Machine)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Hub Sync Service (Daemon)                        │   │
│  │    - Remote file watching (SSH + inotify/FSEvents)  │   │
│  │    - Event queue processing                         │   │
│  │    - Sync orchestration (parallel execution)        │   │
│  │    - Conflict detection engine                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 2. Central State Database (SQLite)                  │   │
│  │    - File checksums (SHA256)                        │   │
│  │    - Sync timestamps per machine                    │   │
│  │    - Conflict resolution log                        │   │
│  │    - Machine health status                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 3. Sync Engine                                      │   │
│  │    - rsync wrapper (incremental, checksum-based)    │   │
│  │    - Bidirectional sync logic                       │   │
│  │    - Retry with exponential backoff                 │   │
│  │    - Bandwidth throttling (optional)                │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 4. PR Aggregation Service                           │   │
│  │    - GitHub CLI integration (gh pr list)            │   │
│  │    - Repository discovery                           │   │
│  │    - PR metadata caching (5-min TTL)                │   │
│  │    - Status enrichment (reviews, checks)            │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 5. Terminal UI Dashboard (Textual)                  │   │
│  │    - Sync Status Panel (4 machines)                 │   │
│  │    - Conversation History Panel                     │   │
│  │    - PR Dashboard Panel                             │   │
│  │    - System Health Panel                            │   │
│  │    - Auto-refresh (3s interval)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Component Details

#### Component 1: Hub Sync Service (Daemon)

**Technology:** Python systemd service
**Responsibilities:**
- Monitor spoke machines for `.claude/` directory changes
- Maintain event queue for sync operations
- Orchestrate bidirectional sync across all spokes
- Detect and resolve conflicts
- Log all sync operations

**Implementation:**
```python
# File: src/sync_hub/daemon.py
class ClaudeSyncHub:
    """Central hub service running on XPS."""

    machines = {
        'rog': {
            'ip': '192.168.68.65',
            'hostname': 'mybox',
            'os': 'linux',
            'user': 'thh3',
            'claude_path': '~/.claude/'
        },
        'mac': {
            'ip': '192.168.68.56',
            'hostname': 'Tomers-MacBook-Pro.local',
            'os': 'mac',
            'user': 'tomerhamam',
            'claude_path': '~/.claude/'
        },
        'nelly': {
            'ip': '192.168.68.60',
            'hostname': 'groisssman',
            'os': 'windows',
            'user': 'nelly',
            'claude_path': '%USERPROFILE%\\.claude\\'
        }
    }

    def start_daemon(self):
        """Start persistent background service."""
        # Initialize database
        # Start file watchers for each spoke
        # Begin event processing loop

    def watch_spoke(self, machine_name):
        """Monitor spoke machine for changes via SSH."""
        # Linux/Mac: SSH + inotifywait
        # Windows: SSH + polling (10s interval)

    def handle_change_event(self, machine, filepath):
        """Process file change notification."""
        # Add to sync queue
        # Trigger sync engine
        # Update database
```

**File Watching Strategy:**

| Platform | Method | Latency | Notes |
|----------|--------|---------|-------|
| Linux (ROG) | SSH + inotifywait | <1s | Real-time events |
| macOS (MAC) | SSH + fswatch | <2s | FSEvents-based |
| Windows (NELLY) | SSH + polling | ~10s | ReadDirectoryChangesW via Python |

---

#### Component 2: Central State Database (SQLite)

**Location:** `/var/lib/claude-sync/sync.db` on XPS
**Purpose:** Track sync state, file checksums, conflict history

**Schema:**
```sql
-- File tracking table
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    filepath TEXT NOT NULL,              -- Relative path from ~/.claude/
    machine TEXT NOT NULL,                -- Source machine
    checksum TEXT NOT NULL,               -- SHA256 hash
    size INTEGER NOT NULL,                -- File size in bytes
    mtime INTEGER NOT NULL,               -- Modification time (Unix timestamp)
    synced_at INTEGER NOT NULL,           -- Last sync time
    UNIQUE(filepath, machine)
);

-- Sync operations log
CREATE TABLE sync_log (
    id INTEGER PRIMARY KEY,
    timestamp INTEGER NOT NULL,           -- Operation time
    operation TEXT NOT NULL,              -- 'pull', 'push', 'conflict'
    source_machine TEXT NOT NULL,
    target_machine TEXT,
    filepath TEXT NOT NULL,
    status TEXT NOT NULL,                 -- 'success', 'failed', 'conflict'
    error_message TEXT
);

-- Machine health status
CREATE TABLE machine_status (
    machine TEXT PRIMARY KEY,
    last_seen INTEGER NOT NULL,           -- Last successful connection
    status TEXT NOT NULL,                 -- 'online', 'offline', 'degraded'
    data_size INTEGER,                    -- Total .claude/ size
    file_count INTEGER,                   -- Number of files
    last_sync INTEGER                     -- Last successful sync
);

-- Conflict resolution history
CREATE TABLE conflicts (
    id INTEGER PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    filepath TEXT NOT NULL,
    machine_a TEXT NOT NULL,
    machine_b TEXT NOT NULL,
    resolution TEXT NOT NULL,             -- 'last-write-wins', 'manual', 'merged'
    winner_machine TEXT,
    notes TEXT
);
```

---

#### Component 3: Sync Engine

**Technology:** Python wrapper around rsync
**Protocol:** rsync over SSH (incremental, checksum-based)

**Sync Modes:**

**Mode 1: Pull (Spoke → Hub)**
```bash
# Pull latest changes from spoke to hub
rsync -avz --checksum --delete \
  ${machine}:~/.claude/ \
  /var/lib/claude-sync/mirrors/${machine}/.claude/
```

**Mode 2: Push (Hub → Spoke)**
```bash
# Push changes from hub to spoke
rsync -avz --checksum \
  /var/lib/claude-sync/mirrors/${source_machine}/.claude/ \
  ${target_machine}:~/.claude/
```

**Conflict Detection:**
```python
def detect_conflict(filepath):
    """Check if file modified on multiple machines since last sync."""

    # Get all machine versions
    versions = db.query("""
        SELECT machine, checksum, mtime
        FROM files
        WHERE filepath = ?
    """, (filepath,))

    # Check if 2+ machines have different checksums
    unique_checksums = set(v['checksum'] for v in versions)

    if len(unique_checksums) > 1:
        # Conflict detected!
        return True, versions

    return False, None
```

**Conflict Resolution Strategies:**

1. **Last-Write-Wins (Default)**
   - Keep version with most recent `mtime`
   - Log discarded versions for manual recovery
   - Fast, automatic, risk of data loss

2. **Append-Only Merge (history.jsonl)**
   - Merge entries chronologically by timestamp
   - No data loss for append-only files
   - Safe for conversation logs

3. **Manual Resolution (User Prompt)**
   - Dashboard shows conflict notification
   - User selects winning version
   - Both versions preserved for inspection

---

#### Component 4: PR Aggregation Service

**Technology:** GitHub CLI (`gh`) wrapper
**Refresh Interval:** 5 minutes (cache to avoid rate limits)

**Implementation:**
```python
# File: src/pr_dashboard/pr_service.py
import subprocess
import json
from datetime import datetime, timedelta

class PRDashboardService:
    """Aggregate PRs from all accessible repositories."""

    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)

    def fetch_all_prs(self):
        """Fetch PRs from all repositories with caching."""

        # Check cache
        if self._is_cache_valid():
            return self.cache['prs']

        # Fetch fresh data
        repos = self._discover_repositories()
        all_prs = []

        for repo in repos:
            prs = self._fetch_prs_for_repo(repo)
            all_prs.extend(prs)

        # Update cache
        self.cache = {
            'prs': all_prs,
            'fetched_at': datetime.now()
        }

        return all_prs

    def _discover_repositories(self):
        """Find all repos user has access to."""
        cmd = ['gh', 'repo', 'list', '--limit', '100', '--json', 'nameWithOwner']
        result = subprocess.run(cmd, capture_output=True, text=True)
        repos = json.loads(result.stdout)
        return [r['nameWithOwner'] for r in repos]

    def _fetch_prs_for_repo(self, repo):
        """Fetch open PRs for specific repository."""
        cmd = [
            'gh', 'pr', 'list',
            '--repo', repo,
            '--state', 'open',
            '--json', 'number,title,updatedAt,isDraft,reviewDecision,author'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return []  # Repo not accessible or no PRs

        prs = json.loads(result.stdout)

        # Enrich with repo name
        for pr in prs:
            pr['repository'] = repo

        return prs

    def group_by_repo(self, prs):
        """Group PRs by repository for display."""
        by_repo = {}
        for pr in prs:
            repo = pr['repository']
            if repo not in by_repo:
                by_repo[repo] = []
            by_repo[repo].append(pr)
        return by_repo
```

**API Rate Limiting:**
- GitHub API: 5,000 requests/hour (authenticated)
- Strategy: 5-minute cache + repository batching
- Fallback: Increase cache TTL if rate limited

---

#### Component 5: Terminal UI Dashboard (Textual)

**Technology:** Textual framework + Rich (reuse Epic 7 patterns)
**Refresh Rate:** 3 seconds (auto-refresh)

**Panel Architecture:**

```python
# File: src/claude_sync/dashboard/sync_dashboard.py
from textual.app import App
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive

# Reuse Epic 7 base panel
from src.dashboard.panels.base_panel import BasePanel

class SyncStatusPanel(BasePanel):
    """Display sync status for all 4 machines."""

    machine_statuses = reactive({})

    async def refresh_data(self):
        """Query hub service for machine statuses."""
        # Read from SQLite database
        self.machine_statuses = self.hub.get_machine_statuses()

    def render_content(self) -> str:
        """Render sync status table."""
        return f"""
┌─ Sync Status ────────────────────────────────────────┐
│ Overall: ✅ 4/4 Machines Synced                      │
│ Last Sync: {self.last_sync_time}                     │
│                                                       │
│ Machine    Status  Last Sync        Files  Conflicts │
│ ─────────────────────────────────────────────────────│
│ 🖥️  XPS     🟢 Hub  (always current)  {xps_files}  0 │
│ 🐧 ROG     🟢 OK   {rog_sync} ago    {rog_files}  0 │
│ 🍎 MAC     🟢 OK   {mac_sync} ago    {mac_files}  0 │
│ 🪟 NELLY   🟡 SLOW {nelly_sync} ago  {nelly_files} 1│
│                                                       │
│ Sync Rate: {sync_rate} MB/s | Avg Latency: {latency}│
└───────────────────────────────────────────────────────┘
        """

class ConversationHistoryPanel(BasePanel):
    """Browse recent conversations grouped by project."""

    conversations = reactive([])

    async def refresh_data(self):
        """Load conversations from hub database."""
        # Query SQLite for recent history entries
        self.conversations = self.hub.get_recent_conversations(limit=20)

    def render_content(self) -> str:
        """Render conversation list."""
        # Group by project, show timestamps, machine origin
        pass

class PRDashboardPanel(BasePanel):
    """Display pending PRs grouped by repository."""

    prs = reactive([])

    async def refresh_data(self):
        """Fetch latest PRs from service."""
        self.prs = self.pr_service.fetch_all_prs()

    def render_content(self) -> str:
        """Render PR list with status badges."""
        pass

class ClaudeSyncDashboard(App):
    """Main dashboard application."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
        ("tab", "focus_next", "Next Panel"),
        ("shift+tab", "focus_previous", "Previous Panel"),
    ]

    def compose(self):
        yield Header()
        with Container():
            yield SyncStatusPanel()
            yield ConversationHistoryPanel()
            yield PRDashboardPanel()
        yield Footer()
```

---

## 4. Data Flow Architecture

### 4.1 Event-Based Sync Flow

```
┌────────────────────────────────────────────────────────────┐
│                    Sync Flow Diagram                       │
└────────────────────────────────────────────────────────────┘

[1] User creates conversation on ROG
    ~/.claude/history.jsonl modified
            │
            ▼
[2] Hub detects change (inotify via SSH)
    Event: {machine: 'rog', file: 'history.jsonl', type: 'modify'}
            │
            ▼
[3] Hub pulls latest from ROG
    rsync rog:~/.claude/history.jsonl → /var/lib/claude-sync/mirrors/rog/
            │
            ▼
[4] Hub updates database
    UPDATE files SET checksum=?, mtime=?, synced_at=? WHERE machine='rog' AND filepath='history.jsonl'
            │
            ▼
[5] Hub pushes to other spokes
    Parallel rsync:
    - /var/lib/.../rog/history.jsonl → xps:~/.claude/history.jsonl
    - /var/lib/.../rog/history.jsonl → mac:~/.claude/history.jsonl
    - /var/lib/.../rog/history.jsonl → nelly:~/.claude/history.jsonl
            │
            ▼
[6] Dashboard updates (auto-refresh)
    Sync Status Panel: ROG → 🟢 OK (3s ago)
```

**Total Latency: <10 seconds** (2s detect + 2s pull + 3s push + 3s refresh)

---

### 4.2 Conflict Resolution Flow

```
[1] Conversation modified on ROG (timestamp: T1)
[2] Same conversation modified on MAC (timestamp: T2, T2 > T1)
[3] Hub detects both changes
            │
            ▼
[4] Conflict Detection
    SELECT * FROM files WHERE filepath='projects/moderator/context.json'
    Results:
    - ROG: checksum=abc123, mtime=T1
    - MAC: checksum=def456, mtime=T2  ← Different!
            │
            ▼
[5] Apply Resolution Strategy
    Strategy: Last-Write-Wins (configured)
    Winner: MAC (T2 > T1)
            │
            ▼
[6] Sync Winner to All Machines
    rsync mac:projects/moderator/context.json → [rog, xps, nelly]
            │
            ▼
[7] Log Conflict Resolution
    INSERT INTO conflicts (filepath, machine_a, machine_b, resolution, winner_machine)
    VALUES ('projects/moderator/context.json', 'rog', 'mac', 'last-write-wins', 'mac')
            │
            ▼
[8] Dashboard Alert (if configured)
    Alerts Panel: "⚠️ Conflict resolved: context.json (MAC version kept)"
```

---

## 5. Technology Stack

### 5.1 Core Technologies

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Hub Service** | Python | 3.9+ | Proven in Moderator, async support |
| **File Sync** | rsync | 3.2+ | Battle-tested, efficient incremental sync |
| **Database** | SQLite | 3.35+ | Lightweight, no server required |
| **Terminal UI** | Textual | 0.40+ | Epic 7 proven working, modern TUI |
| **SSH Client** | OpenSSH | 8.0+ | Cross-platform, secure |
| **GitHub API** | GitHub CLI (`gh`) | 2.0+ | Official, well-maintained |
| **File Watching** | watchdog (Python) | 2.0+ | Cross-platform file monitoring |

### 5.2 Dependencies

**Python Packages:**
```
requirements.txt:
textual>=0.40.0
rich>=13.0.0
watchdog>=2.0.0
paramiko>=3.0.0  # SSH library (fallback)
```

**System Dependencies:**
- rsync
- ssh (OpenSSH client)
- gh (GitHub CLI)
- inotify-tools (Linux)
- fswatch (macOS - via Homebrew)

---

## 6. Deployment Architecture

### 6.1 Hub Service Deployment (XPS)

**Installation:**
```bash
# 1. Clone repository
cd /opt
git clone <repo> claude-sync-manager
cd claude-sync-manager

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create service user
sudo useradd -r -s /bin/bash claude-sync

# 4. Create data directories
sudo mkdir -p /var/lib/claude-sync/mirrors/{rog,mac,nelly}
sudo chown -R claude-sync:claude-sync /var/lib/claude-sync

# 5. Install systemd service
sudo cp scripts/claude-sync-hub.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable claude-sync-hub
sudo systemctl start claude-sync-hub
```

**Systemd Service:**
```ini
# /etc/systemd/system/claude-sync-hub.service
[Unit]
Description=Claude Sync Manager Hub Service
After=network.target

[Service]
Type=simple
User=claude-sync
Group=claude-sync
WorkingDirectory=/opt/claude-sync-manager
ExecStart=/usr/bin/python3 -m src.sync_hub.daemon
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 6.2 Dashboard Launch

**Manual Launch:**
```bash
python -m src.claude_sync.dashboard.sync_dashboard
```

**Alias (add to ~/.bashrc):**
```bash
alias claude-dashboard='python /opt/claude-sync-manager/src/claude_sync/dashboard/sync_dashboard.py'
```

---

## 7. Security Considerations

### 7.1 Authentication

- **SSH Keys:** ed25519 keys, passwordless authentication
- **Key Management:** Keys already distributed, no new key generation needed
- **Credentials:** `.credentials.json` EXCLUDED from sync (contains API keys)

### 7.2 Data Protection

**In Transit:**
- All sync via SSH (encrypted channel)
- rsync over SSH tunnel

**At Rest:**
- Hub mirrors: `/var/lib/claude-sync/` with 0700 permissions
- Database: `/var/lib/claude-sync/sync.db` with 0600 permissions
- Spoke data: Unchanged permissions (user-owned)

### 7.3 Attack Surface

**Threats:**
1. SSH key compromise → Mitigated by key rotation policy
2. Hub service exploit → Run as non-root user, sandboxed
3. Man-in-the-middle → SSH encryption + host key verification
4. Credentials leak → `.credentials.json` excluded from sync

---

## 8. Monitoring & Observability

### 8.1 Metrics Collected

**Per Machine:**
- Last successful sync timestamp
- Sync latency (ms)
- Data transfer rate (MB/s)
- File count
- Total data size
- Online/offline status

**System-Wide:**
- Sync success rate (%)
- Conflict count
- Average sync latency
- Total bandwidth used

### 8.2 Health Checks

```python
def check_machine_health(machine):
    """Determine machine health status."""

    last_seen = db.query("SELECT last_seen FROM machine_status WHERE machine = ?", (machine,))
    now = time.time()

    if now - last_seen > 300:  # 5 minutes
        return 'offline'
    elif now - last_seen > 60:  # 1 minute
        return 'degraded'
    else:
        return 'online'
```

### 8.3 Alerts

**Dashboard Alerts:**
- Machine offline >5 minutes
- Sync failed 3+ times consecutively
- Conflict detected (requires resolution)
- Disk space low on hub (<10% free)

**Log Levels:**
- DEBUG: File change events
- INFO: Successful sync operations
- WARNING: Retries, degraded machines
- ERROR: Sync failures, conflicts

---

## 9. Error Handling & Recovery

### 9.1 Network Failures

**Scenario:** Spoke machine unreachable

**Handling:**
1. Mark machine as 'offline' in database
2. Skip sync for that machine
3. Retry with exponential backoff (1s, 2s, 4s, 8s, max 60s)
4. Alert user via dashboard if offline >5 minutes

### 9.2 Sync Failures

**Scenario:** rsync command fails

**Handling:**
1. Log error with full details
2. Retry up to 3 times
3. If still failing, mark as 'failed' in sync_log
4. Alert user, continue with other machines

### 9.3 Conflict Loops

**Scenario:** Two machines keep modifying same file

**Prevention:**
1. After conflict resolution, lock file for 30 seconds
2. Sync winner version to all machines
3. Wait for all machines to acknowledge
4. Only then unlock for new changes

### 9.4 Service Crashes

**Scenario:** Hub service crashes

**Recovery:**
- systemd restarts service automatically (RestartSec=10)
- On startup, service checks database for incomplete operations
- Resume pending syncs from queue

---

## 10. Performance Optimization

### 10.1 Parallel Execution

**Epic 5 Validation:** Sync to 3 spokes simultaneously

```python
import concurrent.futures

def sync_to_all_spokes(source_machine, filepath):
    """Push file to all spokes in parallel."""

    targets = [m for m in machines.keys() if m != source_machine]

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(sync_to_spoke, target, filepath): target
            for target in targets
        }

        for future in concurrent.futures.as_completed(futures):
            target = futures[future]
            try:
                result = future.result()
                log.info(f"Synced to {target}: {result}")
            except Exception as e:
                log.error(f"Sync to {target} failed: {e}")
```

**Expected Speedup:** 3x (3 sequential syncs → 1 parallel batch)

### 10.2 Incremental Sync

**rsync Flags:**
- `--checksum`: Only transfer changed blocks
- `--compress`: Compress data in transit
- `--delete`: Remove deleted files on target

**Bandwidth Savings:** ~90% for unchanged files

### 10.3 Caching

**GitHub PR Cache:**
- TTL: 5 minutes
- Reduces API calls from 720/hour → 12/hour (60x reduction)

---

## 11. Testing Strategy

### 11.1 Unit Tests

- Conflict detection logic
- Checksum calculation
- Timestamp comparison
- Path normalization (cross-platform)

### 11.2 Integration Tests

- Full sync flow (ROG → XPS → MAC → NELLY)
- Conflict resolution end-to-end
- Network failure handling
- Parallel execution correctness

### 11.3 Real-World Validation

- 7-day production usage (Phase 6)
- Metrics collection: sync latency, success rate
- User feedback: Tomer's daily use

---

## 12. Future Enhancements

**Phase 2 (Not in MVP):**
- Encryption for credentials sync
- Compression for large files
- Bandwidth throttling (configurable)
- Web UI (in addition to terminal UI)
- Mobile app (view-only dashboard)
- Multi-user support (family/team sync)
- Cloud backup (S3/Dropbox integration)

---

## 13. Success Criteria

**Functional:**
- ✅ Sync works across all 4 machines
- ✅ Latency <10 seconds
- ✅ Zero data loss
- ✅ Conflicts detected and resolved

**System Validation:**
- ✅ Epic 5 (Parallel Execution) provides measurable speedup
- ✅ Epic 7 (Dashboard) components reused successfully
- ✅ Epic 6 (Monitor) tracks real metrics
- ✅ Epic 4 (QA) catches real issues

**User Value:**
- ✅ Tomer uses tool daily
- ✅ Problem solved (conversation continuity)
- ✅ PR dashboard useful

---

**Document Version:** 1.0
**Architecture Sign-Off:** Winston (Lead Architect)
**Review Date:** 2025-01-16
**Status:** Ready for Implementation

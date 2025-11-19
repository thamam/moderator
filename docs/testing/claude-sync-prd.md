# Product Requirements Document (PRD)
## Claude Sync Manager

**Product Name:** Claude Sync Manager
**Version:** 1.0 (MVP)
**Product Manager:** John
**Created:** 2025-01-16 (Phase 1, Task 1.4)
**Status:** Ready for Implementation

---

## 1. Executive Summary

### 1.1 Product Vision

Claude Sync Manager enables seamless Claude Code CLI experience across multiple machines by automatically synchronizing conversation history, project context, and configurations in real-time, with a unified dashboard for monitoring sync status and GitHub pull requests.

### 1.2 Problem Statement

**Current Pain:** Tomer works with Claude Code across 4 machines (2 Linux, 1 macOS, 1 Windows). When switching machines, conversation history is isolated per machine, breaking context continuity and forcing redundant explanations. Additionally, tracking pull requests across multiple repositories requires visiting each repo individually.

**Impact:**
- Lost productivity from context re-establishment (est. 10-15 min per context switch)
- Missed PR reviews due to fragmented visibility
- Frustration from repetitive explanations to Claude
- Risk of inconsistent development environments

### 1.3 Solution

A hub-and-spoke synchronization system with:
1. **Real-time sync** of Claude Code data across all 4 machines (<10s latency)
2. **Unified PR dashboard** aggregating all repositories in one view
3. **Terminal UI** for monitoring sync status and system health
4. **Automatic conflict resolution** for simultaneous edits
5. **Zero configuration** after initial setup (runs as background service)

### 1.4 Success Metrics

**Primary (Functional):**
- Sync latency: <10 seconds from file change to propagation
- Sync success rate: >99%
- Data integrity: Zero data loss over 7-day testing period
- Uptime: >99.9% (hub service)

**Secondary (User Value):**
- Daily active use: Tomer uses tool every day for 1 week
- Problem solved: Tomer reports conversation continuity across machines
- PR visibility: All pending PRs visible in single dashboard view
- Time saved: <5 seconds to check all PR statuses (vs. ~2 min visiting repos)

**Tertiary (System Validation - Moderator Testing):**
- Moderator generates working code with <5 bugs
- QA gates catch ≥3 real issues
- Ever-Thinker provides ≥3 valuable improvement suggestions
- Learning system demonstrates ≥1 adaptive behavior change
- Parallel execution provides ≥1.5x speedup

---

## 2. User Personas

### Primary User: Tomer (Multi-Machine Developer)

**Demographics:**
- Role: Software developer / AI enthusiast
- Experience: Advanced technical user
- Environment: 4 machines (XPS always-on hub, ROG laptop, MAC laptop, NELLY Windows desktop)
- Workflow: Switches between machines based on location and task

**Goals:**
- Seamless Claude Code experience regardless of which machine is used
- Quick visibility into all pending PRs across repos
- Minimal manual intervention (set-and-forget)

**Pain Points:**
- Loses conversation context when switching machines
- Wastes time visiting multiple GitHub repos to check PR status
- Inconsistent development environment across machines

**Technical Proficiency:**
- Comfortable with terminal/CLI
- Understands SSH, rsync, system services
- Can debug issues if well-documented

---

## 3. Product Requirements

### 3.1 MVP Scope (In Scope)

**Core Features:**
1. Real-time bidirectional sync of `~/.claude/` directory
2. Hub-and-spoke architecture (XPS as central hub)
3. Event-based file watching (Linux/macOS/Windows)
4. Automatic conflict detection and resolution
5. GitHub PR aggregation dashboard
6. Terminal UI with 4 panels (sync status, conversations, PRs, health)
7. Systemd service for hub daemon
8. Basic error handling and retry logic

**Out of Scope (Future Phases):**
- Web UI (terminal only for MVP)
- Mobile app
- Cloud backup (S3/Dropbox)
- Multi-user/team sync
- Encryption for credentials sync
- Compression for large files
- Bandwidth throttling
- Custom sync schedules

### 3.2 Technical Requirements

**Platform Support:**
- Linux (Ubuntu 20.04+) - ROG, XPS
- macOS (11.0+) - MAC
- Windows 11 - NELLY

**Dependencies:**
- Python 3.9+
- rsync 3.2+
- OpenSSH 8.0+
- GitHub CLI (`gh`) 2.0+
- SQLite 3.35+

**Network:**
- Local network (192.168.68.0/22)
- Passwordless SSH between all machines (already configured)
- XPS always-on hub (24/7 availability)

---

## 4. Epic Breakdown

### Epic 1: Hub Sync Service

**Goal:** Implement persistent background service on XPS that monitors spoke machines and orchestrates sync operations.

**User Story:**
As the system, I need a reliable hub service running on XPS that monitors all spoke machines for changes and keeps all machines synchronized within 10 seconds.

**Stories:**
1. **Story 1.1:** Hub Daemon Service
   - Systemd service on XPS
   - File watching for 3 spoke machines (ROG, MAC, NELLY)
   - Event queue processing
   - Auto-restart on crash

2. **Story 1.2:** Remote File Watching
   - SSH + inotify for Linux (ROG)
   - SSH + fswatch for macOS (MAC)
   - SSH + polling for Windows (NELLY, 10s interval)
   - Change event detection

3. **Story 1.3:** Central State Database
   - SQLite schema (files, sync_log, machine_status, conflicts)
   - File checksum tracking (SHA256)
   - Sync timestamp management
   - Health status tracking

**Acceptance Criteria:**
- [ ] Hub service starts on XPS boot
- [ ] Service monitors all 3 spokes concurrently
- [ ] File changes detected within 10 seconds
- [ ] Database tracks all file states
- [ ] Service restarts automatically on crash

**Dependencies:** None (foundational)

**Effort Estimate:** 2 days

---

### Epic 2: Sync Engine

**Goal:** Build robust bidirectional sync mechanism using rsync over SSH with conflict detection and resolution.

**User Story:**
As a user, when I modify Claude Code data on any machine, I want those changes automatically propagated to all other machines within 10 seconds, with conflicts detected and resolved intelligently.

**Stories:**
1. **Story 2.1:** Pull Mechanism (Spoke → Hub)
   - rsync wrapper for pulling changes
   - Checksum-based incremental sync
   - Error handling and retry logic
   - Logging and metrics

2. **Story 2.2:** Push Mechanism (Hub → Spokes)
   - Bidirectional sync logic
   - Parallel execution (sync to 3 spokes simultaneously)
   - Target machine health check before push
   - Rollback on failure

3. **Story 2.3:** Conflict Detection
   - Detect files modified on multiple machines
   - Compare checksums and timestamps
   - Log conflicts to database
   - Generate conflict reports

4. **Story 2.4:** Conflict Resolution
   - Last-write-wins strategy (default)
   - Append-only merge for `history.jsonl`
   - Manual resolution prompt (future: UI)
   - Preserve both versions for recovery

**Acceptance Criteria:**
- [ ] Sync latency <10 seconds (95th percentile)
- [ ] Parallel execution works without race conditions
- [ ] Conflicts detected with 100% accuracy
- [ ] Zero data loss during conflict resolution
- [ ] Failed syncs retry with exponential backoff

**Dependencies:** Epic 1 (Hub Service)

**Effort Estimate:** 1.5 days

---

### Epic 3: PR Aggregation Service

**Goal:** Unified view of all pending GitHub pull requests across all repositories.

**User Story:**
As Tomer, I want to see all my pending PRs in one place, grouped by repository with status indicators (ready/review/changes/approved), so I don't miss review requests.

**Stories:**
1. **Story 3.1:** GitHub CLI Integration
   - `gh pr list` wrapper
   - Repository discovery (`gh repo list`)
   - PR metadata fetching (number, title, state, reviews)
   - Rate limit handling

2. **Story 3.2:** PR Status Enrichment
   - Review decision tracking (approved, changes requested, pending)
   - CI/CD status checks
   - Author and assignee info
   - Last update timestamp

3. **Story 3.3:** Caching Layer
   - 5-minute cache TTL
   - Avoid GitHub API rate limits (5000/hour)
   - Cache invalidation on user request
   - Background refresh

**Acceptance Criteria:**
- [ ] Fetches PRs from all accessible repositories
- [ ] Groups PRs by repository
- [ ] Status badges accurate (🟢/🟡/🔴)
- [ ] Cache reduces API calls by >90%
- [ ] Refresh completes within 10 seconds

**Dependencies:** None (independent)

**Effort Estimate:** 1 day

---

### Epic 4: Terminal UI Dashboard

**Goal:** Real-time terminal dashboard showing sync status, conversation history, and PRs using Textual framework (reuse Epic 7 patterns).

**User Story:**
As Tomer, I want a live dashboard showing which machines are synced, recent conversations, and pending PRs, so I have visibility into system status at a glance.

**Stories:**
1. **Story 4.1:** Dashboard Framework
   - Reuse Epic 7 `MonitorDashboardApp` base
   - 4-panel layout
   - Auto-refresh (3-second interval)
   - Keyboard shortcuts (Tab, Q, ?)

2. **Story 4.2:** Sync Status Panel
   - 4 machines with status icons (🟢/🟡/🔴)
   - Last sync timestamp per machine
   - File counts and conflicts
   - Sync rate and latency metrics

3. **Story 4.3:** Conversation History Panel
   - Recent 20 conversations
   - Grouped by project
   - Timestamp and machine origin
   - Expandable for full history

4. **Story 4.4:** PR Dashboard Panel
   - All open PRs grouped by repository
   - Status badges (ready, review, changes, approved)
   - Summary counts (critical, pending, approved)
   - Expandable for PR details

5. **Story 4.5:** System Health Panel
   - Hub service status
   - Database size
   - Network connectivity
   - Disk space warnings

**Acceptance Criteria:**
- [ ] Dashboard launches without errors
- [ ] All 4 panels render correctly
- [ ] Auto-refresh works (3s interval)
- [ ] Keyboard shortcuts functional
- [ ] Reuses ≥80% of Epic 7 BasePanel code

**Dependencies:** Epics 1, 2, 3 (data sources)

**Effort Estimate:** 1 day

---

### Epic 5: Error Handling & Recovery

**Goal:** Robust error handling for network failures, sync failures, service crashes, and edge cases.

**User Story:**
As a user, when network issues or failures occur, I want the system to handle them gracefully, retry automatically, and alert me only when manual intervention is needed.

**Stories:**
1. **Story 5.1:** Network Failure Handling
   - Mark machine as offline after timeout
   - Exponential backoff retry (1s, 2s, 4s, 8s, max 60s)
   - Alert user if offline >5 minutes
   - Continue syncing available machines

2. **Story 5.2:** Sync Failure Recovery
   - Log detailed error messages
   - Retry failed syncs up to 3 times
   - Mark as failed in database if exhausted
   - User notification via dashboard

3. **Story 5.3:** Service Crash Recovery
   - Systemd auto-restart (RestartSec=10)
   - Resume pending operations from database
   - No data loss on crash
   - Health check on startup

**Acceptance Criteria:**
- [ ] Network failures don't crash service
- [ ] Failed syncs retry automatically
- [ ] Service restarts within 10 seconds of crash
- [ ] No data loss during failures
- [ ] User alerted only for persistent failures (3+ retries)

**Dependencies:** Epics 1, 2

**Effort Estimate:** 0.5 days

---

## 5. User Stories (Detailed)

### 5.1 Core Sync Functionality

**Story:** Real-Time Conversation Sync
**Priority:** P0 (Must Have)
**Persona:** Tomer

**As** Tomer,
**I want** my Claude Code conversations to sync automatically across all machines,
**So that** I can switch machines without losing context or repeating myself.

**Acceptance Criteria:**
- [ ] When I create a conversation on ROG, it appears on XPS/MAC/NELLY within 10 seconds
- [ ] When I continue a conversation on MAC, the updated history syncs to all machines
- [ ] Conversation history (`history.jsonl`) merges chronologically without data loss
- [ ] Project context (`projects/`) syncs bidirectionally
- [ ] File edit history (`file-history/`) preserved across machines

**Test Scenarios:**
1. Create conversation on ROG → Verify on MAC within 10s
2. Continue conversation on MAC → Verify on ROG within 10s
3. Modify same conversation on ROG and MAC simultaneously → Conflict detected and resolved
4. Take MAC offline → ROG/NELLY still sync → MAC syncs when back online

---

**Story:** Configuration Sync
**Priority:** P1 (Should Have)
**Persona:** Tomer

**As** Tomer,
**I want** my Claude Code settings, commands, and agents synchronized,
**So that** each machine has the same development environment.

**Acceptance Criteria:**
- [ ] `settings.json` syncs across machines (except platform-specific fields)
- [ ] Custom slash commands (`commands/`) available on all machines
- [ ] Custom agents (`agents/`) accessible everywhere
- [ ] SSH hooks preserved (platform-appropriate versions)

**Exclusions:**
- `.credentials.json` (security - excluded from sync)
- `settings.local.json` (machine-specific by design)
- `statusLine.command` (platform-specific bash/PowerShell)

---

### 5.2 PR Dashboard

**Story:** Unified PR View
**Priority:** P0 (Must Have)
**Persona:** Tomer

**As** Tomer,
**I want** to see all my pending PRs across all repositories in one dashboard,
**So that** I don't miss review requests or forget about pending work.

**Acceptance Criteria:**
- [ ] Dashboard shows all open PRs from accessible repositories
- [ ] PRs grouped by repository
- [ ] Status indicators: 🟢 Approved, 🟡 Awaiting Review, 🔴 Changes Requested
- [ ] Shows PR metadata: number, title, author, last update
- [ ] Refresh interval: 5 minutes (cached to avoid rate limits)
- [ ] Manual refresh available (keyboard shortcut)

**Test Scenarios:**
1. Create PR in `moderator` repo → Appears in dashboard within 5 min
2. Request changes on PR → Status updates to 🔴
3. Approve PR → Status updates to 🟢
4. Merge PR → PR disappears from open list

---

### 5.3 System Monitoring

**Story:** Sync Status Visibility
**Priority:** P1 (Should Have)
**Persona:** Tomer

**As** Tomer,
**I want** to see which machines are synced and when the last sync occurred,
**So that** I know the system is working correctly.

**Acceptance Criteria:**
- [ ] Dashboard shows all 4 machines with status (🟢 Online, 🟡 Degraded, 🔴 Offline)
- [ ] Last sync timestamp displayed per machine (e.g., "5s ago")
- [ ] File count and data size shown per machine
- [ ] Conflict count visible (ideally 0)
- [ ] Sync rate (MB/s) and latency (ms) metrics

---

## 6. Non-Functional Requirements

### 6.1 Performance

- **Sync Latency:** <10 seconds (95th percentile)
- **Dashboard Refresh:** 3 seconds (auto-refresh)
- **PR Fetch:** <10 seconds for initial load
- **Parallel Execution:** Sync to 3 spokes in <5 seconds (vs. 15s sequential)

### 6.2 Reliability

- **Uptime:** >99.9% (hub service)
- **Sync Success Rate:** >99%
- **Data Integrity:** Zero data loss (100% validated)
- **Crash Recovery:** Auto-restart within 10 seconds

### 6.3 Security

- **Authentication:** SSH key-based (no passwords)
- **Credentials Protection:** `.credentials.json` excluded from sync
- **Data in Transit:** Encrypted (SSH tunnel)
- **Database Permissions:** 0600 (owner read/write only)

### 6.4 Usability

- **Setup Time:** <15 minutes (after dependencies installed)
- **Configuration:** Minimal (machines, paths)
- **Dashboard Launch:** Single command (`claude-dashboard`)
- **Error Messages:** Clear, actionable, with resolution steps

### 6.5 Maintainability

- **Code Quality:** Pass QA gates (pylint, flake8, bandit)
- **Test Coverage:** >80% for core sync logic
- **Documentation:** README, architecture docs, inline comments
- **Logging:** Structured logs (JSON) for debugging

---

## 7. Technical Constraints

### 7.1 Infrastructure

- **Hub Machine:** XPS must be always-on (24/7)
- **Network:** All machines on same local network (192.168.68.0/22)
- **SSH:** Passwordless authentication configured
- **Disk Space:** XPS needs 1GB free for mirrors

### 7.2 Dependencies

- **Required:**
  - Python 3.9+
  - rsync 3.2+
  - OpenSSH 8.0+
  - GitHub CLI (`gh`) 2.0+

- **Optional:**
  - inotify-tools (Linux)
  - fswatch (macOS)

### 7.3 Data Limits

- **Total Data:** ~824 MB across 4 machines (current)
- **Growth:** Plan for 2GB total (2.5x headroom)
- **Single File:** No limit (rsync handles large files)

---

## 8. Risk Assessment

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Hub service crashes | Medium | High | Systemd auto-restart + health monitoring |
| Network partition | Low | Medium | Offline detection + retry logic |
| Data corruption | Low | Critical | Checksum validation + conflict detection |
| Disk space exhaustion | Low | Medium | Monitor disk usage + alerts |
| SSH key compromise | Low | Critical | Key rotation policy + audit logs |

### 8.2 User Experience Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Sync too slow (>10s) | Medium | High | Parallel execution + incremental rsync |
| Too many conflicts | Medium | Medium | Last-write-wins default + merge for append-only |
| Dashboard crashes | Low | Low | Textual framework proven (Epic 7) |
| Confusing errors | Medium | Medium | Clear error messages + troubleshooting guide |

### 8.3 Project Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep | High | Medium | Strict MVP definition + defer features |
| Implementation bugs | High | High | Comprehensive testing (44 existing tests) |
| MAC offline during testing | Medium | Low | Test with 3 machines, add MAC later |
| Moderator system failures | Medium | Critical | Manual fallback + thorough testing |

---

## 9. Success Criteria (Revisited)

### 9.1 MVP Launch Criteria

**Must Have (Blockers):**
- [ ] Sync works across all 4 machines
- [ ] Latency <10 seconds (95th percentile)
- [ ] Zero data loss over 7-day period
- [ ] Dashboard functional and updating
- [ ] PR aggregation shows all repos

**Should Have (Important):**
- [ ] Conflict resolution working
- [ ] Error handling with retry logic
- [ ] Health monitoring and alerts
- [ ] Logs for debugging

**Nice to Have (Optional):**
- [ ] Performance optimizations
- [ ] Additional dashboard panels
- [ ] Custom sync schedules
- [ ] Compression for large files

### 9.2 Moderator System Validation

**Epic Validation:**
- [ ] Epic 1 (Foundation) - Configuration system works
- [ ] Epic 2 (Learning) - System learns from patterns
- [ ] Epic 3 (Ever-Thinker) - Improvement suggestions valuable
- [ ] Epic 4 (QA) - QA gates catch ≥3 real issues
- [ ] Epic 5 (Parallel Execution) - ≥1.5x speedup measured
- [ ] Epic 6 (Monitoring) - Health metrics tracked
- [ ] Epic 7 (Dashboard) - Code reused successfully

---

## 10. Release Plan

### Phase 1: Discovery & Architecture (Day 1) - ✅ COMPLETE
- [x] Discover Claude data locations
- [x] Analyze file formats and schemas
- [x] Create architecture document
- [x] Generate PRD (this document)

### Phase 2: Sync Engine Implementation (Days 2-3)
- [ ] Implement hub daemon service
- [ ] Build sync engine (pull/push/conflict detection)
- [ ] Add error handling and retry logic
- [ ] Create central SQLite database

### Phase 3: PR Aggregation (Day 4)
- [ ] GitHub CLI integration
- [ ] Repository discovery
- [ ] PR status enrichment
- [ ] Caching layer

### Phase 4: Terminal UI Dashboard (Day 5)
- [ ] Reuse Epic 7 dashboard framework
- [ ] Implement 4 panels (sync, conversations, PRs, health)
- [ ] Add keyboard shortcuts and help screen
- [ ] Test auto-refresh

### Phase 5: Improvement Cycle (Day 6)
- [ ] Run Ever-Thinker on completed code
- [ ] Validate QA integration (find ≥3 issues)
- [ ] Test learning system (≥1 adaptation)
- [ ] Measure parallel execution speedup

### Phase 6: Real-World Validation (Day 7+)
- [ ] Deploy to XPS production
- [ ] 7 days of active usage
- [ ] Collect metrics and feedback
- [ ] Final retrospective

---

## 11. Open Questions

1. **Credentials Sync:** Should we sync `.credentials.json` with encryption, or always exclude?
   - **Recommendation:** Exclude for MVP, add encrypted sync in Phase 2

2. **Conflict Resolution UI:** Manual prompt via dashboard or always auto-resolve?
   - **Recommendation:** Auto-resolve for MVP (last-write-wins), add UI in Phase 2

3. **Polling Interval (Windows):** 10 seconds acceptable or too slow?
   - **Recommendation:** Start with 10s, optimize if user feedback indicates issue

4. **Sync Exclusions:** Any directories beyond `.credentials.json` to exclude?
   - **Recommendation:** Sync everything for MVP, add exclusion list in Phase 2

---

## 12. Appendix

### A. Related Documents

- [Test Plan](claude-sync-manager-test-plan.md)
- [Architecture Document](claude-sync-architecture.md)
- [Data Schema](claude-data-schema.md)
- [Moderator CLAUDE.md](/home/thh3/personal/moderator/CLAUDE.md)

### B. Glossary

- **Hub:** Central always-on machine (XPS) coordinating sync
- **Spoke:** Peripheral machine (ROG, MAC, NELLY) that syncs through hub
- **Conflict:** File modified on 2+ machines since last sync
- **Last-Write-Wins:** Conflict resolution keeping newest modification
- **rsync:** Incremental file sync protocol over SSH

---

**PRD Version:** 1.0
**Product Manager:** John
**Sign-Off:** Ready for Implementation
**Next Steps:** Begin Phase 2 (Sync Engine Implementation)

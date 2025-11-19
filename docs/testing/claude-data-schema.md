# Claude Code CLI Data Schema Documentation

**Purpose:** Technical reference for Claude Sync Manager development
**Created:** 2025-01-16 (Phase 1, Task 1.2)
**Machines Analyzed:** ROG, XPS, MAC, NELLY

---

## Directory Structure

**Common across all platforms (Linux, macOS, Windows):**

```
~/.claude/
├── .credentials.json       # API authentication (⚠️ SENSITIVE)
├── history.jsonl           # Conversation history (JSONL format)
├── settings.json           # User preferences and permissions
├── settings.local.json     # Machine-specific overrides
├── debug/                  # Debug logs and traces
├── file-history/           # File edit history per session
├── ide/                    # IDE integration configurations
├── projects/               # Per-project context and state
├── session-env/            # Session environment variables
├── shell-snapshots/        # Shell command snapshots
├── statsig/                # Analytics and telemetry data
└── todos/                  # Todo tracking data
```

---

## File Formats

### 1. `history.jsonl`

**Format:** JSON Lines (one JSON object per line)
**Purpose:** Complete conversation history across all projects
**Size:** Varies (36KB to 188KB observed)

**Schema:**
```json
{
  "display": "User's message or query text",
  "pastedContents": {},
  "timestamp": 1760192425442,
  "project": "/absolute/path/to/working/directory"
}
```

**Fields:**
- `display` (string): The user's input message or query
- `pastedContents` (object): Any code or text pasted into the conversation (usually empty `{}`)
- `timestamp` (number): Unix timestamp in milliseconds
- `project` (string): Absolute path to the project/working directory

**Notes:**
- Append-only format (new entries added to end)
- No deletion or modification of existing entries
- Chronological order maintained by timestamp
- Cross-platform paths (Linux: `/home/...`, macOS: `/Users/...`, Windows: `C:\Users\...`)

---

### 2. `settings.json`

**Format:** JSON
**Purpose:** User preferences and tool permissions
**Platform-specific:** May contain platform-specific commands (bash vs PowerShell)

**Schema:**
```json
{
  "env": {},
  "permissions": {
    "allow": ["Tool1", "Tool2", ...],
    "deny": [],
    "ask": []
  },
  "statusLine": {
    "type": "command",
    "command": "bash command for custom status line"
  },
  "alwaysThinkingEnabled": false,
  "defaultMode": "plan"
}
```

**Fields:**
- `env` (object): Custom environment variables for Claude Code sessions
- `permissions` (object):
  - `allow` (array): Pre-approved tools (e.g., "Bash", "Read", "WebFetch")
  - `deny` (array): Explicitly denied tools
  - `ask` (array): Tools requiring user confirmation
- `statusLine` (object):
  - `type` (string): Usually "command"
  - `command` (string): Shell command to generate custom prompt (⚠️ Platform-specific!)
- `alwaysThinkingEnabled` (boolean): Enable/disable thinking mode
- `defaultMode` (string): "plan" or "code" mode

**Sync Considerations:**
- `statusLine.command` may differ by platform (Linux/Mac bash vs Windows PowerShell)
- Should we sync this or keep machine-specific?

---

### 3. `settings.local.json`

**Format:** JSON
**Purpose:** Machine-specific overrides (e.g., local paths, machine-specific preferences)

**Observed Schema:**
```json
{
  "statusLine": {
    "type": "command",
    "command": "machine-specific status line command"
  }
}
```

**Sync Decision:** Likely should NOT sync (machine-specific by design)

---

### 4. `.credentials.json`

**Format:** JSON
**Purpose:** API keys and authentication tokens

**⚠️ SECURITY CRITICAL:**
- Contains sensitive authentication data
- MUST NOT be logged or exposed
- Consider exclusion from sync OR encrypted sync only
- Permissions: 0600 (read/write owner only)

**Recommendation:** Exclude from sync or prompt user for encryption key

---

### 5. `projects/` Directory

**Structure:** Subdirectories per project
**Purpose:** Per-project context and state

**Observed:**
- ROG: 26 project directories
- XPS: More extensive
- MAC: 8 project directories
- NELLY: Minimal

**Example Structure:**
```
projects/
├── project-name-1/
│   └── [context files]
├── project-name-2/
│   └── [context files]
└── ...
```

**Sync Strategy:** Full bidirectional sync (essential for context continuity)

---

### 6. `session-env/` Directory

**Structure:** Subdirectories per session
**Purpose:** Environment variables and state for each Claude Code session

**Observed:**
- ROG: 34 session directories
- MAC: 12 session directories

**Sync Consideration:** May contain ephemeral data, review contents before deciding sync strategy

---

### 7. `file-history/` Directory

**Structure:** Subdirectories tracking file edits
**Purpose:** History of file modifications made during Claude Code sessions

**Observed:**
- ROG: 50 file history entries
- MAC: 9 entries

**Sync Strategy:** Full sync (valuable for undo/context recovery)

---

### 8. `todos/` Directory

**Purpose:** Todo tracking across sessions

**Observed:**
- ROG: Present
- XPS: Present
- MAC: 35 todo entries
- NELLY: Present

**Sync Strategy:** Full sync (task continuity across machines)

---

### 9. `debug/`, `shell-snapshots/`, `statsig/`, `ide/`

**Purpose:**
- `debug/`: Debug logs and traces
- `shell-snapshots/`: Command execution snapshots
- `statsig/`: Analytics/telemetry
- `ide/`: IDE-specific configurations

**Sync Strategy:** TBD - may be ephemeral or machine-specific

---

## Data Size Analysis

| Machine | Total Size | Largest Components |
|---------|------------|-------------------|
| XPS (Hub) | 684 MB | Extensive projects, MCP configs |
| ROG | 132 MB | 26 projects, active development |
| MAC | 7.6 MB | 8 projects, lighter usage |
| NELLY | ~36 KB | Minimal setup |

**Total Dataset: ~824 MB**

---

## Cross-Platform Considerations

### Path Differences

**Linux (ROG, XPS):**
```
/home/thh3/.claude/
/home/thh3/work/project-name/
```

**macOS (MAC):**
```
/Users/tomerhamam/.claude/
/Users/tomerhamam/Documents/project-name/
```

**Windows (NELLY):**
```
C:\Users\nelly\.claude\
C:\Users\nelly\Documents\project-name\
```

### Line Endings

- Linux/Mac: LF (`\n`)
- Windows: CRLF (`\r\n`)

**Sync Strategy:** Normalize to LF on sync, convert back on restore if needed

### File Permissions

- Linux/Mac: Strict permissions (0600 for credentials, 0755 for directories)
- Windows: Different permission model (ACLs)

**Sync Strategy:** Preserve permissions metadata, apply appropriately per platform

---

## Sync Exclusions (Recommended)

**Security:**
- `.credentials.json` - Contains API keys (encrypt or exclude)

**Machine-Specific:**
- `settings.local.json` - Machine-specific overrides
- `statusLine.command` in `settings.json` - Platform-specific bash/PowerShell

**Ephemeral (Review):**
- `debug/` - May be large and transient
- `statsig/` - Analytics, may not need sync
- `shell-snapshots/` - Review if needed for continuity

---

## Conflict Resolution Strategy

**Append-Only Files (history.jsonl):**
- Strategy: Merge chronologically by timestamp
- No conflicts expected (append-only)

**Mutable Files (settings.json, projects/):**
- Strategy: Last-write-wins OR manual resolution
- Detect: Compare modification timestamps
- Alert: Notify user via dashboard

**Directories (projects/, file-history/):**
- Strategy: Recursive merge
- New files: Copy bidirectionally
- Modified files: Last-write-wins or prompt

---

## Update Frequency Recommendations

**Real-Time (Event-Based):**
- `history.jsonl` - Every new conversation entry
- `projects/` - On file save/modification
- `file-history/` - On edit completion

**Periodic (Every 5-10 minutes):**
- `settings.json` - Less frequent changes
- `todos/` - Task updates

**On-Demand:**
- Full sync triggered by user
- Initial setup/bootstrap

---

## Implementation Notes

**File Watching:**
- Linux: inotify on `~/.claude/`
- macOS: FSEvents on `~/.claude/`
- Windows: ReadDirectoryChangesW or polling

**Sync Protocol:**
- Primary: rsync over SSH (efficient, incremental)
- Alternative: Custom sync daemon for real-time

**Database:**
- Central index on XPS hub
- SQLite tracking: file checksums, timestamps, sync status

---

**Document Version:** 1.0
**Last Updated:** 2025-01-16
**Next Review:** After implementing prototype sync

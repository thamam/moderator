# BMAD New Chat Context Generator

**Command:** `/bmad-new-chat`
**Purpose:** Generate the perfect context handoff prompt for starting a new chat session while continuing BMAD workflows

---

## Instructions

When this command is invoked:

1. **Read Current Workflow Status**
   - Load `docs/bmm-workflow-status.md`
   - Parse current state information:
     - PROJECT_NAME
     - VERSION_TARGET
     - CURRENT_PHASE
     - CURRENT_WORKFLOW
     - NEXT_ACTION
     - NEXT_COMMAND
     - NEXT_AGENT

2. **Generate Context Statement**
   Create a concise 2-4 sentence context statement that includes:
   - Project name and version target
   - What was just completed (if applicable)
   - Current phase and workflow
   - What's next

3. **Add Agent Command**
   - Include the appropriate agent load command from NEXT_AGENT
   - Format: `/bmad:bmm:agents:{agent-name}`

4. **Format Output**
   Present in a copy-paste ready format with clear instructions

---

## Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 COPY THIS PROMPT FOR YOUR NEW CHAT SESSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Generated context statement - 2-4 sentences]

[Agent load command]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 TIP: Copy everything between the lines above and paste into
your new chat to continue where you left off.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 COPY THIS PROMPT FOR YOUR NEW CHAT SESSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

cam-shift-detector v1.0.0 (ChArUco marker-based detection).

Workflow-init complete. Project is Level 1 brownfield, using
Quick Spec Flow with EBD integration mandatory.

Ready for Phase 2 (Planning) - tech-spec generation.

/bmad:bmm:agents:pm

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 TIP: Copy everything between the lines above and paste into
your new chat to continue where you left off.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Error Handling

**If workflow status file not found:**
```
❌ No workflow status file found.

Have you run workflow-init yet?

To start a new BMAD project:
1. Load analyst agent: /bmad:bmm:agents:analyst
2. Run: *workflow-init
```

**If workflow status is incomplete:**
```
⚠️ Workflow status found but missing key information.

Current status shows:
- Project: [project-name]
- Phase: [current-phase]
- Next: [Try to extract what's available]

Recommended: Start new chat with:
"Working on [project-name]. Need to continue with [phase]."
Then load the appropriate agent.
```

---

## Implementation Notes

- This is a **read-only** command - it never modifies workflow status
- Always generate fresh output based on current workflow status
- Keep context statement concise (2-4 sentences max)
- Make it easy to copy-paste (clear visual boundaries)
- Include helpful tip about how to use it

# Dashboard Manual Verification Checklist

**Epic 7: Real-Time Terminal UI Dashboard (Gear 4)**
**Purpose:** Comprehensive UX quality assurance for production readiness
**Estimated Time:** ~10 minutes

---

## Pre-Launch

- [ ] Textual dependency installed: `pip install textual>=0.40.0`
- [ ] Rich dependency installed: `pip install rich>=13.0.0`
- [ ] MonitorAgent has data (run system for 5+ minutes to collect metrics)
- [ ] Config file has `gear4.dashboard` section in `config/config.yaml`
- [ ] Python 3.9+ installed (for modern type hints)

---

## Launch Test

- [ ] Run: `python -m src.dashboard.monitor_dashboard`
- [ ] Dashboard launches without errors or exceptions
- [ ] All 4 panels visible (Health, Metrics, Alerts, Components)
- [ ] Header displays: "Moderator - System Health Dashboard"
- [ ] Footer shows keyboard shortcuts (Q: Quit, ?: Help)
- [ ] Sub-title shows "Real-time monitoring (Auto-refresh: 3s)"

---

## Health Score Panel (Story 7.2)

- [ ] Health score displays (0-100 range)
- [ ] Status badge present (HEALTHY/DEGRADED/CRITICAL)
- [ ] Status color matches score:
  - 85-100 = Green (HEALTHY)
  - 70-84 = Yellow (DEGRADED)
  - 0-69 = Red (CRITICAL)
- [ ] Component scores table displays 5 rows:
  - Decomposer
  - Executor
  - Learning System
  - QA Manager
  - Monitor Agent
- [ ] Timestamp updates every 3 seconds
- [ ] No data case handled gracefully (yellow message)

---

## Metrics Trends Panel (Story 7.3)

- [ ] 5 sparklines render correctly (ASCII art with Unicode blocks)
- [ ] Sparklines for each metric:
  - Task Success Rate (green sparkline)
  - Task Error Rate (red sparkline)
  - Token Usage (blue sparkline)
  - Avg Task Duration (blue sparkline)
  - System Health Score (green sparkline)
- [ ] Current/Avg/Min/Max values display for each metric
- [ ] Trend arrows display correctly:
  - ↗ (improving)
  - → (stable)
  - ↘ (degrading)
- [ ] Trend colors match direction:
  - Green for improving
  - Yellow for stable
  - Red for degrading
- [ ] Direction-aware logic works (error_rate ↗ when value decreases = green)
- [ ] No data case shows "No metrics data available" message

---

## Alerts Panel (Story 7.4)

- [ ] Alert counts summary bar displays:
  - 🔴 X Critical (red)
  - 🟡 X Warnings (yellow)
  - ✅ X Acknowledged (green)
- [ ] Recent alerts list shows 5 most recent items
- [ ] Alert table columns display: Severity | Metric | Message | Time
- [ ] Severity badges color-coded correctly
- [ ] Messages truncated to 50 characters (with "..." if longer)
- [ ] Timestamps formatted as HH:MM:SS
- [ ] Press Enter on panel: Expands to show all alerts with full details
- [ ] Expanded view shows threshold and actual values
- [ ] Press Enter again: Collapses back to 5 recent alerts
- [ ] No alerts case shows "✅ All systems healthy" in green
- [ ] Last alert timestamp displays when available

---

## Components Panel (Story 7.5)

- [ ] 5 components listed:
  - Task Executor
  - Backend Router
  - Learning System
  - QA Manager
  - Monitor Agent
- [ ] Status indicators display correctly:
  - 🟢 for Operational (green)
  - 🟡 for Degraded (yellow)
  - 🔴 for Error (red)
- [ ] Details column shows useful context (e.g., "Active", "Database connected")
- [ ] Status reflects actual component health
- [ ] Table format is readable and aligned

---

## Keyboard Shortcuts (Story 7.5)

- [ ] Tab: Navigate to next panel (focus moves)
- [ ] Shift+Tab: Navigate to previous panel (focus moves backward)
- [ ] Enter: Expand selected panel (if expandable)
- [ ] Q: Quit dashboard cleanly (no errors on exit)
- [ ] ?: Show help screen (modal overlay appears)
- [ ] ESC: Close help screen (when help is open)
- [ ] ?: Close help screen (press again when help is open)

---

## Help Screen (Story 7.5 - AC 7.5.3)

- [ ] Press '?': Help screen appears as modal overlay
- [ ] Help screen is centered on screen
- [ ] Help screen has border and title "Keyboard Shortcuts"
- [ ] Lists all shortcuts clearly:
  - Navigation: Tab, Shift+Tab, Enter
  - Actions: Q, ?, ESC
  - Auto-Refresh note
- [ ] Help screen has dismiss instructions ("Press ? or ESC to close")
- [ ] Press '?': Help screen closes
- [ ] Press ESC: Help screen closes

---

## Auto-Refresh (Story 7.1)

- [ ] Data updates every 3 seconds automatically
- [ ] Sub-title timestamp advances correctly (HH:MM:SS format)
- [ ] No visible flicker or UI glitches during refresh
- [ ] Panel content updates smoothly
- [ ] No performance degradation after 5+ minutes

---

## Error Handling (Story 7.5 - AC 7.5.4)

- [ ] Simulate panel failure (e.g., raise exception in refresh_data())
- [ ] Failed panel displays error message: "Error loading panel: {error}"
- [ ] Other panels continue to work normally (graceful degradation)
- [ ] Dashboard does not crash
- [ ] Error is logged (check console output)
- [ ] Failed panel shows red error message
- [ ] Can still navigate to other panels

---

## Performance

- [ ] Launch time < 2 seconds (from command to dashboard visible)
- [ ] Refresh time < 100ms (no noticeable lag during auto-refresh)
- [ ] No memory leaks after 5 minutes of continuous running
- [ ] CPU usage reasonable (< 5% when idle between refreshes)
- [ ] Dashboard responsive (no lag when pressing keys)

---

## Visual Quality

- [ ] Panel borders are clean and aligned
- [ ] Colors are consistent and readable
- [ ] Text is not truncated unexpectedly
- [ ] Tables are properly aligned (columns line up)
- [ ] Emoji icons display correctly (🟢🟡🔴🔴✅↗→↘)
- [ ] No overlapping UI elements
- [ ] Dashboard looks professional and polished

---

## Edge Cases

- [ ] No MonitorAgent data: All panels show "No data" messages gracefully
- [ ] Empty alerts: Shows "All systems healthy" message
- [ ] Empty metrics: Shows "No metrics data available" message
- [ ] Missing components: Shows 🔴 Error status indicators
- [ ] Long metric messages: Truncated to 50 chars with "..."
- [ ] Very high/low metric values: Sparklines normalize correctly

---

## Cross-Panel Consistency

- [ ] All panels use consistent color scheme (green=good, red=bad, yellow=warning)
- [ ] All panels have similar header formatting (bold titles)
- [ ] All panels handle errors consistently (red error messages)
- [ ] All panels update on same 3-second interval
- [ ] All panels use same timestamp format (HH:MM:SS)

---

## Final Checks

- [ ] No Python errors or warnings in console
- [ ] No deprecation warnings from Textual or Rich
- [ ] Dashboard can run for 10+ minutes without issues
- [ ] All features from Stories 7.1-7.5 are working
- [ ] Documentation (this checklist) is accurate and complete
- [ ] Dashboard is ready for production use

---

## Sign-Off

**Tester Name:** _______________________
**Date:** _______________________
**Result:** ☐ PASS  ☐ FAIL (list issues below)

**Issues Found:**
1. _______________________
2. _______________________
3. _______________________

**Notes:**
_______________________________________________________________________________________
_______________________________________________________________________________________

---

**Epic 7 Status:**
- ✅ Story 7.1: Dashboard Framework
- ✅ Story 7.2: Health Score Panel
- ✅ Story 7.3: Metrics Trends Panel
- ✅ Story 7.4: Alerts Panel
- ✅ Story 7.5: Component Health + Final Polish

**Dashboard Version:** Gear 4 - Real-Time Terminal UI
**Last Updated:** 2025-11-16
**Status:** Production-Ready ✅

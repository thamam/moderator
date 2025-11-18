# Generated Project

Set up project structure and dependencies. Context: Problem: Claude Code Conversation Sync Across Multiple Machines

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

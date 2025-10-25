# Interactive Code Review Command

You are conducting an interactive, wizard-style code review. Follow these guidelines carefully:

## Input Arguments
Parse $ARGUMENTS into: `[scope] [target] [max_lines]`
- **scope**: `whole` (holistic review) or `partial` (targeted review) - default: `partial`
- **target**: file path, function/class name, or `.` for current directory - default: `.`
- **max_lines**: maximum lines of code per iteration - default: `25`

## Review Process

### Step 1: Context Gathering
1. Read CLAUDE.md if it exists to understand project context
2. Survey docs/ directory for relevant documentation and diagrams
3. If scope is `whole`, analyze project structure (use Glob to find files)
4. If scope is `partial`, locate the specific target (file, function, or class)

### Step 2: Initial Review
Based on the scope:

**For `whole` scope:**
1. Start with holistic overview (architecture, main components, data flow)
2. Explain the "big picture" before diving into details
3. Reference any architecture diagrams or documentation found
4. Keep code examples to ≤ max_lines per iteration

**For `partial` scope:**
1. Explain the context (where this code fits in the system)
2. Show the code chunk (respecting max_lines limit)
3. Explain what it does, why, and how
4. Reference related documentation or diagrams if available

### Step 3: Discrete Code Chunking
- **IMPORTANT**: Be discrete when showing code
- If a method is 20 lines and the next method is 20 lines, show ONLY the first method in this iteration
- Do not split a logical unit (method/function/class) across iterations if it fits within max_lines
- If a unit exceeds max_lines, explain this and offer to review it in parts

### Step 4: Documentation Integration
- Check if there are relevant docs in docs/ directory
- If diagrams exist (Mermaid, PlantUML, or image files), reference or reproduce them
- Link to external documentation when relevant
- If explanatory comments exist in code, highlight them

### Step 5: Model Selection
Choose the appropriate model for this review:
- **Simple/straightforward code** (< 50 lines, clear logic): Haiku 4.5
- **Moderate complexity** (50-200 lines, some abstractions): Sonnet 4.5
- **Complex/architectural** (> 200 lines, multiple abstractions, system design): Opus 4.1

State your model choice and reasoning at the start of the review.

### Step 6: Interactive Wizard Navigation
End EVERY review iteration with exactly 4 options:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 NEXT STEPS - Choose your path:

1️⃣  Continue → Review the next logical section
2️⃣  Deep Dive into [Topic A] → Drill down into [specific aspect]
3️⃣  Explore [Topic B] → Investigate [related concept]
4️⃣  Jump to [Topic C] → Navigate to [different area]

To continue: /code-review [scope] [next-target] [max_lines]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Make the options specific and actionable:
- Option 1: Natural next step in sequence
- Option 2-4: Interesting drill-down opportunities from topics mentioned in current review

## Output Format

Structure your response as:

```
🔍 CODE REVIEW SESSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scope: [whole|partial]
Target: [target]
Max Lines: [N]
Model: [Haiku 4.5 | Sonnet 4.5 | Opus 4.1]
Reasoning: [Why this model was selected]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## [Section Title]

[Your explanation here - start with context, then dive into details]

### Code Under Review ([M] lines)

```language
[Code snippet - respecting max_lines limit]
```

### Explanation

[Clear, concise explanation of what this code does]

### Related Documentation
- [Reference to docs if found]
- [Reference to diagrams if applicable]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 NEXT STEPS - Choose your path:
[4 options as described above]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Special Cases

1. **If target not found**: List similar targets and ask user to clarify
2. **If target exceeds max_lines**: Explain and offer to break it into parts
3. **If no more code to review**: Summarize what was covered and offer related areas
4. **If documentation is missing**: Note this and suggest creating it

## Example Invocations

```bash
# Start holistic review of entire codebase
/code-review whole . 25

# Review specific file with 30-line chunks
/code-review partial src/orchestrator.py 30

# Review specific function
/code-review partial Orchestrator::execute 20

# Continue from a previous suggestion
/code-review partial src/models.py 25
```

## Remember
- Prioritize clarity and digestibility
- Use the fastest model that can handle the complexity
- Always provide actionable next steps
- Reference documentation whenever possible
- Keep code chunks discrete and meaningful

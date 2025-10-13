# Improvement Priority Matrix

## Description
This quadrant diagram visualizes how improvements are prioritized based on implementation effort (X-axis) and impact (Y-axis). It helps the Moderator agent decide which improvements to tackle first by plotting them in a 2x2 matrix with decision boundaries.

## Diagram

```mermaid
quadrantChart
    title Improvement Priority Matrix
    x-axis Low Effort --> High Effort
    y-axis Low Impact --> High Impact
    quadrant-1 Consider Carefully
    quadrant-2 Do First (Quick Wins)
    quadrant-3 Do Last (Low Priority)
    quadrant-4 Plan & Execute (Strategic)

    Add unit tests: [0.3, 0.85]
    Fix security issue: [0.25, 0.95]
    Add README: [0.15, 0.70]
    Performance optimization: [0.70, 0.90]
    Database indexing: [0.40, 0.80]
    API documentation: [0.30, 0.60]
    Code refactoring: [0.75, 0.65]
    UI polish: [0.50, 0.40]
    Add logging: [0.20, 0.50]
    Migrate to TypeScript: [0.95, 0.75]
    Add caching layer: [0.60, 0.85]
    Fix typos: [0.10, 0.15]
    Improve error messages: [0.25, 0.55]
    Add integration tests: [0.50, 0.75]
    Update dependencies: [0.35, 0.45]
```

## Alternative Visualization (Table Format)

| Improvement Type | Effort | Impact | Priority Score | Quadrant | Recommended Action |
|------------------|--------|--------|----------------|----------|-------------------|
| Fix security issue | Low (0.25) | Very High (0.95) | **9.5** | Q2 - Quick Win | ✅ Do Immediately |
| Add unit tests | Low (0.30) | High (0.85) | **8.5** | Q2 - Quick Win | ✅ Do First |
| Database indexing | Medium (0.40) | High (0.80) | **8.0** | Q2 - Quick Win | ✅ Do First |
| Add integration tests | Medium (0.50) | High (0.75) | **7.5** | Q2/Q4 Border | ✅ Do Soon |
| Add README | Very Low (0.15) | High (0.70) | **7.0** | Q2 - Quick Win | ✅ Do First |
| Performance optimization | High (0.70) | Very High (0.90) | **6.3** | Q4 - Strategic | 📋 Plan Carefully |
| Add caching layer | Medium-High (0.60) | High (0.85) | **7.1** | Q4 - Strategic | 📋 Plan & Execute |
| Migrate to TypeScript | Very High (0.95) | High (0.75) | **3.9** | Q1 - Consider | ⚠️ Evaluate Carefully |
| Code refactoring | High (0.75) | Medium (0.65) | **4.3** | Q1 - Consider | ⚠️ Consider Benefits |
| API documentation | Low (0.30) | Medium (0.60) | **6.0** | Q2 - Quick Win | ✅ Do Soon |
| Improve error messages | Low (0.25) | Medium (0.55) | **5.5** | Q2/Q3 Border | 📅 Schedule |
| Update dependencies | Medium (0.35) | Medium (0.45) | **4.5** | Q3 - Low Priority | 📅 Schedule |
| UI polish | Medium (0.50) | Low (0.40) | **3.2** | Q3 - Low Priority | ⏰ Do Last |
| Add logging | Low (0.20) | Medium (0.50) | **5.0** | Q3 - Low Priority | 📅 Schedule |
| Fix typos | Very Low (0.10) | Very Low (0.15) | **1.5** | Q3 - Low Priority | ⏰ Do Last |

## Scoring Algorithm

```python
class ImprovementPrioritizer:
    def calculate_priority_score(self, improvement):
        """
        Priority Score = (Impact * Impact Weight) - (Effort * Effort Weight)

        Higher score = Higher priority
        """
        IMPACT_WEIGHT = 10
        EFFORT_WEIGHT = 3  # Effort counts against priority

        score = (improvement.impact * IMPACT_WEIGHT) - (improvement.effort * EFFORT_WEIGHT)
        return score

    def estimate_impact(self, improvement_type, context):
        """
        Impact scoring (0.0 - 1.0):
        - Security fixes: 0.9-1.0 (critical)
        - Performance: 0.7-0.9 (high)
        - Testing: 0.7-0.9 (high)
        - Documentation: 0.5-0.7 (medium)
        - Refactoring: 0.4-0.7 (medium-low)
        - Polish/cosmetic: 0.1-0.3 (low)
        """
        impact_scores = {
            'security': 0.90,
            'performance': 0.80,
            'testing': 0.75,
            'documentation': 0.60,
            'refactoring': 0.55,
            'polish': 0.30
        }

        base_score = impact_scores.get(improvement_type, 0.50)

        # Adjust based on context
        if context.has_users:
            if improvement_type == 'security':
                base_score = min(1.0, base_score + 0.1)

        if context.test_coverage < 0.5:
            if improvement_type == 'testing':
                base_score = min(1.0, base_score + 0.15)

        return base_score

    def estimate_effort(self, improvement_description, codebase_size):
        """
        Effort scoring (0.0 - 1.0):
        - Very Low: 0.0-0.2 (< 1 hour)
        - Low: 0.2-0.4 (1-3 hours)
        - Medium: 0.4-0.6 (3-8 hours)
        - High: 0.6-0.8 (8-16 hours)
        - Very High: 0.8-1.0 (16+ hours)
        """
        # Estimate based on keywords
        if 'migrate' in improvement_description.lower():
            return 0.90
        elif 'refactor all' in improvement_description.lower():
            return 0.85
        elif 'optimization' in improvement_description.lower():
            return 0.70
        elif 'add caching' in improvement_description.lower():
            return 0.60
        elif 'add tests' in improvement_description.lower():
            return 0.40
        elif 'fix' in improvement_description.lower():
            return 0.30
        elif 'add' in improvement_description.lower():
            return 0.25
        else:
            return 0.50  # Default medium

    def prioritize_improvements(self, improvements):
        """
        Returns improvements sorted by priority score
        """
        scored_improvements = []

        for imp in improvements:
            imp.impact = self.estimate_impact(imp.type, imp.context)
            imp.effort = self.estimate_effort(imp.description, imp.codebase_size)
            imp.priority_score = self.calculate_priority_score(imp)

            scored_improvements.append(imp)

        # Sort by priority score (descending)
        scored_improvements.sort(key=lambda x: x.priority_score, reverse=True)

        return scored_improvements
```

## Quadrant Definitions

### Q2: Do First (Quick Wins)
**Characteristics**:
- Low to Medium effort
- High impact
- Quick ROI

**Examples**:
- Fix security vulnerabilities
- Add unit tests for critical paths
- Add README documentation
- Database indexing

**Strategy**: Execute immediately in improvement cycle

### Q4: Plan & Execute (Strategic)
**Characteristics**:
- High effort
- High impact
- Requires planning

**Examples**:
- Performance optimization (algorithmic changes)
- Add caching layer
- Comprehensive integration tests

**Strategy**: Break into smaller tasks, execute over multiple cycles

### Q1: Consider Carefully
**Characteristics**:
- High effort
- Medium to Low impact
- Requires justification

**Examples**:
- Large refactoring projects
- Technology migrations
- Architectural changes

**Strategy**: Evaluate if benefits justify effort, defer if not critical

### Q3: Do Last (Low Priority)
**Characteristics**:
- Low to Medium effort
- Low impact
- Nice to have

**Examples**:
- UI polish
- Fix typos
- Minor logging improvements

**Strategy**: Execute only if time/resources available, often skipped

## Decision Boundaries

### Priority Score Thresholds
```python
PRIORITY_THRESHOLDS = {
    'critical': 8.0,     # Do immediately
    'high': 6.0,         # Do in current cycle
    'medium': 4.0,       # Schedule for next cycle
    'low': 2.0,          # Consider if resources available
    'defer': 0.0         # Skip or defer indefinitely
}
```

### Improvement Cycle Selection
```python
def select_improvements_for_cycle(improvements, max_improvements=3):
    """
    Select top N improvements for current cycle based on:
    1. Priority score
    2. Effort budget
    3. Dependencies
    """
    prioritized = prioritize_improvements(improvements)

    selected = []
    total_effort = 0.0
    MAX_EFFORT_PER_CYCLE = 2.0  # Total effort points per cycle

    for imp in prioritized:
        if len(selected) >= max_improvements:
            break

        if total_effort + imp.effort <= MAX_EFFORT_PER_CYCLE:
            # Check dependencies
            if all(dep in selected for dep in imp.dependencies):
                selected.append(imp)
                total_effort += imp.effort

    return selected
```

## Impact Factors

### Security Impact
- **Critical**: Exploitable vulnerability
- **High**: Potential data exposure
- **Medium**: Best practice violation
- **Low**: Minor hardening

### Performance Impact
- Measured as % improvement in:
  - Response time
  - Resource usage
  - Throughput
- **High impact**: > 30% improvement
- **Medium impact**: 10-30% improvement
- **Low impact**: < 10% improvement

### Testing Impact
- Test coverage increase
- Critical path coverage
- Bug detection probability
- **High impact**: Covers critical paths
- **Medium impact**: Improves coverage
- **Low impact**: Minor additions

### Documentation Impact
- User-facing: High impact
- Developer-facing: Medium impact
- Internal-only: Low impact

## References
- PRD: moderator-prd.md - Section 5.3 "Improvement Cycle" (lines 330-360)
- Architecture: archetcture.md - "The Ever-Thinker" continuous improvement (lines 167-174)
- CLAUDE.md: Ever-Thinker - Improver component (lines 173-179)

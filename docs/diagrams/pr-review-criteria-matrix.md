# PR Review Criteria Matrix

## Description
This table/matrix diagram shows the PR review criteria categories (code_quality, testing, documentation, acceptance), pass/fail conditions for each, weighted scoring system, and auto-approve thresholds.

## Review Criteria Matrix

| Category | Criteria | Pass Condition | Weight | Points | Blocking? |
|----------|----------|----------------|--------|--------|-----------|
| **CODE_QUALITY** | | | **35%** | **/35** | |
| | Passes linting | No lint errors | 8% | /8 | Yes |
| | Follows conventions | Style guide adhered | 7% | /7 | No |
| | No obvious bugs | Code review passed | 10% | /10 | Yes |
| | Appropriate complexity | Complexity score < 10 | 10% | /10 | No |
| **TESTING** | | | **30%** | **/30** | |
| | Has tests | Tests exist for new code | 10% | /10 | Yes |
| | Tests pass | All tests green | 15% | /15 | Yes |
| | Adequate coverage | Coverage ≥ 80% for new code | 5% | /5 | No |
| **DOCUMENTATION** | | | **20%** | **/20** | |
| | Code is commented | Complex code has comments | 8% | /8 | No |
| | README updated | README reflects changes | 7% | /7 | No |
| | API docs current | Public APIs documented | 5% | /5 | No |
| **ACCEPTANCE** | | | **15%** | **/15** | |
| | Meets criteria | All acceptance criteria met | 10% | /10 | Yes |
| | No scope creep | Changes within task scope | 3% | /3 | No |
| | Backwards compatible | No breaking changes | 2% | /2 | No |
| **TOTAL** | | | **100%** | **/100** | |

## Scoring System

### Score Calculation
```python
def calculate_pr_score(pr_review):
    """
    Calculate weighted score for PR (0-100)
    """
    score = 0

    # Code Quality (35 points)
    if pr_review.passes_linting:
        score += 8
    if pr_review.follows_conventions:
        score += 7
    if pr_review.no_obvious_bugs:
        score += 10
    if pr_review.appropriate_complexity:
        score += 10

    # Testing (30 points)
    if pr_review.has_tests:
        score += 10
    if pr_review.tests_pass:
        score += 15
    if pr_review.adequate_coverage:
        score += 5

    # Documentation (20 points)
    if pr_review.code_is_commented:
        score += 8
    if pr_review.readme_updated:
        score += 7
    if pr_review.api_docs_current:
        score += 5

    # Acceptance (15 points)
    if pr_review.meets_acceptance_criteria:
        score += 10
    if pr_review.no_scope_creep:
        score += 3
    if pr_review.backwards_compatible:
        score += 2

    return score
```

### Pass/Fail Determination
```python
def determine_pr_status(pr_review):
    """
    Determine if PR passes or fails review
    """
    # Check blocking criteria first
    blocking_failures = []

    if not pr_review.passes_linting:
        blocking_failures.append("Linting errors present")

    if not pr_review.no_obvious_bugs:
        blocking_failures.append("Code has obvious bugs")

    if not pr_review.has_tests:
        blocking_failures.append("Missing tests for new code")

    if not pr_review.tests_pass:
        blocking_failures.append("Tests are failing")

    if not pr_review.meets_acceptance_criteria:
        blocking_failures.append("Does not meet acceptance criteria")

    # If any blocking criteria fail, PR fails
    if blocking_failures:
        return {
            'status': 'FAIL',
            'blocking_issues': blocking_failures,
            'can_auto_approve': False
        }

    # Calculate score for non-blocking criteria
    score = calculate_pr_score(pr_review)

    # Determine status based on score
    if score >= 90:
        return {'status': 'EXCELLENT', 'score': score, 'can_auto_approve': True}
    elif score >= 80:
        return {'status': 'PASS', 'score': score, 'can_auto_approve': True}
    elif score >= 70:
        return {'status': 'PASS_WITH_NOTES', 'score': score, 'can_auto_approve': False}
    else:
        return {'status': 'NEEDS_IMPROVEMENT', 'score': score, 'can_auto_approve': False}
```

## Auto-Approve Thresholds

### Auto-Approve Conditions
```python
AUTO_APPROVE_THRESHOLDS = {
    'min_score': 80,
    'required_blocking': [
        'passes_linting',
        'no_obvious_bugs',
        'has_tests',
        'tests_pass',
        'meets_acceptance_criteria'
    ],
    'min_coverage': 0.80,
    'max_complexity': 10
}

def can_auto_approve(pr_review):
    """
    Determine if PR can be auto-approved
    """
    score = calculate_pr_score(pr_review)

    # Must meet minimum score
    if score < AUTO_APPROVE_THRESHOLDS['min_score']:
        return False

    # All blocking criteria must pass
    for criterion in AUTO_APPROVE_THRESHOLDS['required_blocking']:
        if not getattr(pr_review, criterion):
            return False

    # Must meet coverage threshold
    if pr_review.coverage < AUTO_APPROVE_THRESHOLDS['min_coverage']:
        return False

    # Must not exceed complexity limit
    if pr_review.complexity > AUTO_APPROVE_THRESHOLDS['max_complexity']:
        return False

    return True
```

## Detailed Criteria Definitions

### Code Quality Criteria

**Passes Linting**
- Condition: No errors from linter (ESLint, Pylint, etc.)
- Blocking: Yes
- Points: 8

**Follows Conventions**
- Condition: Code follows project style guide
- Blocking: No
- Points: 7

**No Obvious Bugs**
- Condition: No logic errors, null checks present, error handling appropriate
- Blocking: Yes
- Points: 10

**Appropriate Complexity**
- Condition: Cyclomatic complexity < 10, functions < 50 lines
- Blocking: No
- Points: 10

### Testing Criteria

**Has Tests**
- Condition: Unit tests exist for all new functions/classes
- Blocking: Yes
- Points: 10

**Tests Pass**
- Condition: All tests (unit, integration) pass
- Blocking: Yes
- Points: 15

**Adequate Coverage**
- Condition: New code has ≥ 80% test coverage
- Blocking: No
- Points: 5

### Documentation Criteria

**Code is Commented**
- Condition: Complex logic has explanatory comments
- Blocking: No
- Points: 8

**README Updated**
- Condition: README reflects new features/changes
- Blocking: No
- Points: 7

**API Docs Current**
- Condition: Public APIs have documentation
- Blocking: No
- Points: 5

### Acceptance Criteria

**Meets Acceptance Criteria**
- Condition: All task acceptance criteria checked off
- Blocking: Yes
- Points: 10

**No Scope Creep**
- Condition: Changes are within task scope
- Blocking: No
- Points: 3

**Backwards Compatible**
- Condition: No breaking changes to public APIs
- Blocking: No
- Points: 2

## Review Decision Flow

```python
class PRReviewDecision:
    def make_decision(self, pr_review):
        """
        Make final review decision
        """
        status = determine_pr_status(pr_review)

        if status['status'] == 'FAIL':
            return ReviewDecision(
                action='REQUEST_CHANGES',
                feedback=self.generate_feedback(status['blocking_issues']),
                can_merge=False
            )

        elif status['status'] == 'EXCELLENT' and can_auto_approve(pr_review):
            return ReviewDecision(
                action='AUTO_APPROVE',
                feedback="Excellent work! Auto-approved.",
                can_merge=True
            )

        elif status['status'] in ['PASS', 'PASS_WITH_NOTES']:
            if can_auto_approve(pr_review):
                return ReviewDecision(
                    action='APPROVE',
                    feedback=self.generate_positive_feedback(pr_review),
                    can_merge=True
                )
            else:
                return ReviewDecision(
                    action='APPROVE_WITH_NOTES',
                    feedback=self.generate_improvement_suggestions(pr_review),
                    can_merge=True
                )

        else:  # NEEDS_IMPROVEMENT
            return ReviewDecision(
                action='REQUEST_IMPROVEMENTS',
                feedback=self.generate_improvement_feedback(pr_review),
                can_merge=False
            )
```

## References
- PRD: moderator-prd.md - Section 7.3 "PR Review Criteria" (lines 472-495)
- CLAUDE.md: "PR review system" in architecture overview

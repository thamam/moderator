#!/bin/bash
# Checkpoint 4: Code Quality (QA Gates)
#
# Purpose: Run QA tools on generated code (validates Epic 4 integration)
# Pass Criteria: Bandit catches ≥1 real security issue (proves QA works)
# Score: Bandit issues + Pylint score + Flake8 violations
#
# This checkpoint validates that Epic 4 (QA Integration) is working correctly
# by running the integrated QA tools on generated code.
#
# Usage: ./checkpoint-4-qa-gates.sh <code-directory>

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Input validation
if [ $# -ne 1 ]; then
    echo "Usage: $0 <code-directory>"
    echo "Example: $0 state/proj_abc123/artifacts/task_001/generated/"
    exit 1
fi

CODE_DIR="$1"

if [ ! -d "$CODE_DIR" ]; then
    echo "Error: Code directory not found: $CODE_DIR"
    exit 1
fi

echo "============================================="
echo "📍 CHECKPOINT 4: Code Quality (QA Gates)"
echo "============================================="
echo ""
echo "This checkpoint validates Epic 4 (QA Integration) is working."
echo "Running QA tools: Bandit, Pylint, Flake8"
echo ""

# Find Python files
PYTHON_FILES=$(find "$CODE_DIR" -name "*.py" -type f)
FILE_COUNT=$(echo "$PYTHON_FILES" | wc -w)

if [ $FILE_COUNT -eq 0 ]; then
    echo -e "${RED}Error: No Python files found in $CODE_DIR${NC}"
    exit 1
fi

echo "Found $FILE_COUNT Python file(s) to analyze"
echo ""

# Initialize results
BANDIT_ISSUES=0
BANDIT_HIGH=0
BANDIT_MEDIUM=0
BANDIT_LOW=0
PYLINT_SCORE=0.0
FLAKE8_VIOLATIONS=0

# Run Bandit (Security)
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Running Bandit (Security Scanner)${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

if command -v bandit &> /dev/null; then
    # Run bandit and capture output
    BANDIT_OUTPUT=$(mktemp)
    bandit -r "$CODE_DIR" -f txt -o "$BANDIT_OUTPUT" 2>&1 || true

    # Parse results
    BANDIT_HIGH=$(grep -c "Severity: High" "$BANDIT_OUTPUT" || echo "0")
    BANDIT_MEDIUM=$(grep -c "Severity: Medium" "$BANDIT_OUTPUT" || echo "0")
    BANDIT_LOW=$(grep -c "Severity: Low" "$BANDIT_OUTPUT" || echo "0")
    BANDIT_ISSUES=$((BANDIT_HIGH + BANDIT_MEDIUM + BANDIT_LOW))

    echo "Results:"
    echo "  🚨 High severity: $BANDIT_HIGH"
    echo "  ⚠️  Medium severity: $BANDIT_MEDIUM"
    echo "  ℹ️  Low severity: $BANDIT_LOW"
    echo "  Total issues: $BANDIT_ISSUES"
    echo ""

    if [ $BANDIT_HIGH -gt 0 ]; then
        echo -e "${RED}High severity issues found:${NC}"
        grep -A 5 "Severity: High" "$BANDIT_OUTPUT" || true
        echo ""
    fi

    # Save full report
    cp "$BANDIT_OUTPUT" "checkpoint-4-bandit-report.txt"
    rm "$BANDIT_OUTPUT"
else
    echo -e "${YELLOW}Warning: Bandit not installed. Install with: pip install bandit${NC}"
    echo ""
fi

# Run Pylint (Code Quality)
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Running Pylint (Code Quality)${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

if command -v pylint &> /dev/null; then
    # Run pylint and capture score
    PYLINT_OUTPUT=$(mktemp)
    for pyfile in $PYTHON_FILES; do
        pylint "$pyfile" >> "$PYLINT_OUTPUT" 2>&1 || true
    done

    # Extract score (format: "Your code has been rated at 7.50/10")
    PYLINT_SCORE=$(grep "rated at" "$PYLINT_OUTPUT" | tail -1 | sed -n 's/.*rated at \([0-9.]*\).*/\1/p' || echo "0.0")

    echo "Results:"
    echo "  Score: $PYLINT_SCORE / 10.0"
    echo ""

    # Show issues if score is low
    if (( $(echo "$PYLINT_SCORE < 8.0" | bc -l) )); then
        echo -e "${YELLOW}Issues found (score < 8.0):${NC}"
        tail -20 "$PYLINT_OUTPUT"
        echo ""
    fi

    # Save full report
    cp "$PYLINT_OUTPUT" "checkpoint-4-pylint-report.txt"
    rm "$PYLINT_OUTPUT"
else
    echo -e "${YELLOW}Warning: Pylint not installed. Install with: pip install pylint${NC}"
    echo ""
fi

# Run Flake8 (Style)
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Running Flake8 (PEP 8 Style)${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

if command -v flake8 &> /dev/null; then
    # Run flake8 and count violations
    FLAKE8_OUTPUT=$(mktemp)
    flake8 "$CODE_DIR" >> "$FLAKE8_OUTPUT" 2>&1 || true

    FLAKE8_VIOLATIONS=$(wc -l < "$FLAKE8_OUTPUT")

    echo "Results:"
    echo "  PEP 8 violations: $FLAKE8_VIOLATIONS"
    echo ""

    if [ $FLAKE8_VIOLATIONS -gt 0 ]; then
        echo -e "${YELLOW}Top violations:${NC}"
        head -20 "$FLAKE8_OUTPUT"
        echo ""
    fi

    # Save full report
    cp "$FLAKE8_OUTPUT" "checkpoint-4-flake8-report.txt"
    rm "$FLAKE8_OUTPUT"
else
    echo -e "${YELLOW}Warning: Flake8 not installed. Install with: pip install flake8${NC}"
    echo ""
fi

# Evaluate Epic 4 Validation
echo "============================================="
echo "EPIC 4 VALIDATION (QA Integration)"
echo "============================================="
echo ""

EPIC4_PASS=false
EPIC4_STATUS=""

if [ $BANDIT_ISSUES -ge 1 ]; then
    EPIC4_PASS=true
    EPIC4_STATUS="${GREEN}✅ PASS${NC}"
    echo -e "Status: $EPIC4_STATUS"
    echo ""
    echo "Bandit caught $BANDIT_ISSUES security issue(s)."
    echo "This proves Epic 4 (QA Integration) is working correctly!"
else
    EPIC4_STATUS="${YELLOW}⚠️  MARGINAL${NC}"
    echo -e "Status: $EPIC4_STATUS"
    echo ""
    echo "Bandit found 0 security issues."
    echo "This could mean:"
    echo "  1) Generated code has excellent security (unlikely on first run)"
    echo "  2) Epic 4 integration is not working properly"
    echo "  3) Test case doesn't exercise security-sensitive code"
    echo ""
    echo "Consider adding a test that generates code with known security issues"
    echo "(e.g., SQL injection, command injection, hardcoded secrets)."
fi

echo ""

# Overall Code Quality Assessment
echo "============================================="
echo "CHECKPOINT 4 RESULTS"
echo "============================================="
echo -e "Epic 4 Validation: $EPIC4_STATUS"
echo ""
echo "QA Tool Results:"
echo "  Bandit (Security):"
echo "    - High severity: $BANDIT_HIGH"
echo "    - Medium severity: $BANDIT_MEDIUM"
echo "    - Low severity: $BANDIT_LOW"
echo "    - Total issues: $BANDIT_ISSUES"
echo ""
echo "  Pylint (Code Quality):"
echo "    - Score: $PYLINT_SCORE / 10.0"
echo ""
echo "  Flake8 (Style):"
echo "    - PEP 8 violations: $FLAKE8_VIOLATIONS"
echo ""

# Save results to file
RESULTS_FILE="checkpoint-4-results.txt"
cat > "$RESULTS_FILE" << EOF
Checkpoint 4: Code Quality (QA Gates)
======================================
Epic 4 Validation: $EPIC4_STATUS

Pass Criteria:
- Bandit catches ≥1 real security issue (proves QA integration works)

QA Tool Results:

Bandit (Security Scanner):
- High severity issues: $BANDIT_HIGH
- Medium severity issues: $BANDIT_MEDIUM
- Low severity issues: $BANDIT_LOW
- Total issues: $BANDIT_ISSUES

Pylint (Code Quality):
- Score: $PYLINT_SCORE / 10.0

Flake8 (PEP 8 Style):
- Violations: $FLAKE8_VIOLATIONS

Code Directory: $CODE_DIR
Files Analyzed: $FILE_COUNT

Detailed Reports:
- checkpoint-4-bandit-report.txt
- checkpoint-4-pylint-report.txt
- checkpoint-4-flake8-report.txt

Timestamp: $(date)
EOF

echo "Results saved to: $RESULTS_FILE"
echo "Detailed reports saved to: checkpoint-4-*-report.txt"
echo ""

# Exit with appropriate code
if [ "$EPIC4_PASS" = true ]; then
    exit 0  # Pass
else
    exit 1  # Marginal
fi

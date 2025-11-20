#!/bin/bash
# Checkpoint 5: Test Coverage
#
# Purpose: Measure test coverage of generated code
# Pass Criteria: ≥60% coverage (Target: ≥80%)
# Score: Coverage percentage + test count
#
# Usage: ./checkpoint-5-coverage.sh <code-directory>

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
echo "📍 CHECKPOINT 5: Test Coverage"
echo "============================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not installed.${NC}"
    echo "Install with: pip install pytest pytest-cov"
    exit 1
fi

# Find test files
TEST_FILES=$(find "$CODE_DIR" -name "test_*.py" -o -name "*_test.py" -type f)
TEST_COUNT=$(echo "$TEST_FILES" | wc -w)

if [ $TEST_COUNT -eq 0 ]; then
    echo -e "${RED}Error: No test files found in $CODE_DIR${NC}"
    echo "Expected files matching: test_*.py or *_test.py"
    echo ""

    # Save failure results
    cat > checkpoint-5-results.txt << EOF
Checkpoint 5: Test Coverage
===========================
Status: ❌ FAIL
Score: 0 / 100

Error: No test files found

Expected:
- Files matching pattern: test_*.py or *_test.py
- Located in: $CODE_DIR

Timestamp: $(date)
EOF

    exit 1
fi

echo "Found $TEST_COUNT test file(s)"
echo ""

# Run pytest with coverage
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Running pytest with coverage${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Create temporary output file
PYTEST_OUTPUT=$(mktemp)
COVERAGE_OUTPUT=$(mktemp)

# Run pytest with coverage
cd "$CODE_DIR"
pytest --cov=. --cov-report=term --cov-report=html --cov-report=json -v > "$PYTEST_OUTPUT" 2>&1 || true
cd - > /dev/null

# Parse results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0
COVERAGE_PERCENT=0

# Extract test counts
if grep -q "passed" "$PYTEST_OUTPUT"; then
    TESTS_PASSED=$(grep -oP '\d+(?= passed)' "$PYTEST_OUTPUT" | tail -1 || echo "0")
fi

if grep -q "failed" "$PYTEST_OUTPUT"; then
    TESTS_FAILED=$(grep -oP '\d+(?= failed)' "$PYTEST_OUTPUT" | tail -1 || echo "0")
fi

TESTS_TOTAL=$((TESTS_PASSED + TESTS_FAILED))

# Extract coverage percentage from JSON report (most reliable)
if [ -f "$CODE_DIR/.coverage.json" ]; then
    COVERAGE_PERCENT=$(python3 -c "import json; data=json.load(open('$CODE_DIR/.coverage.json')); print(int(data['totals']['percent_covered']))" 2>/dev/null || echo "0")
elif [ -f "$CODE_DIR/coverage.json" ]; then
    COVERAGE_PERCENT=$(python3 -c "import json; data=json.load(open('$CODE_DIR/coverage.json')); print(int(data['totals']['percent_covered']))" 2>/dev/null || echo "0")
else
    # Fallback: parse from terminal output (less reliable)
    COVERAGE_PERCENT=$(grep -oP 'TOTAL.*\K\d+(?=%)' "$PYTEST_OUTPUT" | tail -1 || echo "0")
fi

# Display results
echo "Test Results:"
echo "  Total tests: $TESTS_TOTAL"
echo "  Passed: $TESTS_PASSED"
echo "  Failed: $TESTS_FAILED"
echo ""
echo "Coverage Results:"
echo "  Coverage: $COVERAGE_PERCENT%"
echo ""

# Show failed tests if any
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed tests:${NC}"
    grep -A 3 "FAILED" "$PYTEST_OUTPUT" || true
    echo ""
fi

# Determine status
STATUS=""
if [ $COVERAGE_PERCENT -ge 95 ]; then
    STATUS="${GREEN}✅ EXCELLENT${NC}"
elif [ $COVERAGE_PERCENT -ge 80 ]; then
    STATUS="${GREEN}✅ PASS (TARGET)${NC}"
elif [ $COVERAGE_PERCENT -ge 60 ]; then
    STATUS="${YELLOW}⚠️  PASS (MINIMUM)${NC}"
else
    STATUS="${RED}❌ FAIL${NC}"
fi

# Output results
echo "============================================="
echo "CHECKPOINT 5 RESULTS"
echo "============================================="
echo -e "Status: $STATUS"
echo "Coverage: $COVERAGE_PERCENT%"
echo ""
echo "Breakdown:"
echo "  Test files: $TEST_COUNT"
echo "  Total tests: $TESTS_TOTAL"
echo "  Passed: $TESTS_PASSED"
echo "  Failed: $TESTS_FAILED"
echo "  Coverage: $COVERAGE_PERCENT%"
echo ""

# Evaluate test quality
echo "Test Quality Assessment:"
if [ $TESTS_TOTAL -eq 0 ]; then
    echo "  ❌ No tests were executed (even though test files exist)"
elif [ $TESTS_FAILED -gt 0 ]; then
    echo "  ❌ Some tests are failing - fix before claiming coverage"
elif [ $COVERAGE_PERCENT -lt 60 ]; then
    echo "  ❌ Coverage below minimum threshold (60%)"
elif [ $COVERAGE_PERCENT -lt 80 ]; then
    echo "  ⚠️  Coverage meets minimum but below target (80%)"
else
    echo "  ✅ Coverage meets or exceeds target"
fi

echo ""

# Save results to file
RESULTS_FILE="checkpoint-5-results.txt"
cat > "$RESULTS_FILE" << EOF
Checkpoint 5: Test Coverage
============================
Status: $STATUS
Coverage: $COVERAGE_PERCENT%

Test Execution:
- Test files found: $TEST_COUNT
- Total tests run: $TESTS_TOTAL
- Tests passed: $TESTS_PASSED
- Tests failed: $TESTS_FAILED

Coverage Metrics:
- Line coverage: $COVERAGE_PERCENT%

Pass Criteria:
- Minimum: ≥60% coverage
- Target: ≥80% coverage
- Excellent: ≥95% coverage

Quality Assessment:
$(if [ $TESTS_FAILED -gt 0 ]; then
    echo "- ❌ $TESTS_FAILED test(s) failing"
elif [ $COVERAGE_PERCENT -ge 80 ]; then
    echo "- ✅ Good test coverage (≥80%)"
elif [ $COVERAGE_PERCENT -ge 60 ]; then
    echo "- ⚠️  Minimum coverage met (60-79%)"
else
    echo "- ❌ Insufficient coverage (<60%)"
fi)

Code Directory: $CODE_DIR

Detailed Reports:
- HTML coverage report: $CODE_DIR/htmlcov/index.html
- JSON coverage report: $CODE_DIR/coverage.json

Full pytest output:
$(cat "$PYTEST_OUTPUT")

Timestamp: $(date)
EOF

echo "Results saved to: $RESULTS_FILE"

# Save detailed reports
cp "$PYTEST_OUTPUT" "checkpoint-5-pytest-output.txt"

if [ -d "$CODE_DIR/htmlcov" ]; then
    echo "HTML coverage report: $CODE_DIR/htmlcov/index.html"
fi

echo ""

# Cleanup
rm "$PYTEST_OUTPUT"

# Exit with appropriate code
if [ $COVERAGE_PERCENT -ge 60 ] && [ $TESTS_FAILED -eq 0 ]; then
    exit 0  # Pass
else
    exit 1  # Fail
fi

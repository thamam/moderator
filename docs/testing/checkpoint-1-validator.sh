#!/bin/bash
# Checkpoint 1: Problem Understanding Validator
#
# Purpose: Validate that Moderator asks clarifying questions after receiving seed input
# Pass Criteria: ≥3 clarifying questions asked
# Score: /20 points
#
# Usage: ./checkpoint-1-validator.sh <moderator-conversation-log>

set -euo pipefail

# Configuration
MIN_QUESTIONS=3
TARGET_QUESTIONS=5
EXCELLENT_QUESTIONS=7

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Input validation
if [ $# -ne 1 ]; then
    echo "Usage: $0 <moderator-conversation-log>"
    echo "Example: $0 moderator-conversation.log"
    exit 1
fi

LOG_FILE="$1"

if [ ! -f "$LOG_FILE" ]; then
    echo "Error: Log file not found: $LOG_FILE"
    exit 1
fi

echo "============================================="
echo "📍 CHECKPOINT 1: Problem Understanding"
echo "============================================="
echo ""

# Extract questions from log
# Look for lines ending with '?' which indicate questions
grep -E '\?' "$LOG_FILE" > questions.txt || true

# Count questions
QUESTION_COUNT=$(wc -l < questions.txt)

echo "Questions asked by Moderator: $QUESTION_COUNT"
echo ""

# Show the questions
if [ $QUESTION_COUNT -gt 0 ]; then
    echo "--- Questions Found ---"
    cat questions.txt
    echo "----------------------"
    echo ""
fi

# Evaluate quality manually (requires human judgment)
echo "Quality Evaluation:"
echo "Please review the questions above and answer:"
echo ""
read -p "How many questions are truly clarifying (not rhetorical)? " CLARIFYING_COUNT
read -p "How many questions show deep understanding of the problem domain? " INSIGHTFUL_COUNT

# Calculate score
SCORE=0
STATUS=""

if [ $QUESTION_COUNT -ge $EXCELLENT_QUESTIONS ] && [ $CLARIFYING_COUNT -ge 5 ] && [ $INSIGHTFUL_COUNT -ge 2 ]; then
    STATUS="${GREEN}✅ EXCELLENT${NC}"
    SCORE=20
elif [ $QUESTION_COUNT -ge $TARGET_QUESTIONS ] && [ $CLARIFYING_COUNT -ge 3 ]; then
    STATUS="${GREEN}✅ PASS (TARGET)${NC}"
    SCORE=15
elif [ $QUESTION_COUNT -ge $MIN_QUESTIONS ] && [ $CLARIFYING_COUNT -ge 2 ]; then
    STATUS="${YELLOW}⚠️  MARGINAL${NC}"
    SCORE=10
else
    STATUS="${RED}❌ FAIL${NC}"
    SCORE=5
fi

# Output results
echo ""
echo "============================================="
echo "CHECKPOINT 1 RESULTS"
echo "============================================="
echo -e "Status: $STATUS"
echo "Score: $SCORE / 20 points"
echo ""
echo "Breakdown:"
echo "  Total questions: $QUESTION_COUNT"
echo "  Clarifying questions: $CLARIFYING_COUNT"
echo "  Insightful questions: $INSIGHTFUL_COUNT"
echo ""

# Save results to file
RESULTS_FILE="checkpoint-1-results.txt"
cat > "$RESULTS_FILE" << EOF
Checkpoint 1: Problem Understanding
====================================
Status: $STATUS
Score: $SCORE / 20

Metrics:
- Total questions asked: $QUESTION_COUNT
- Clarifying questions: $CLARIFYING_COUNT
- Insightful questions: $INSIGHTFUL_COUNT

Pass Criteria:
- Minimum: ≥3 questions (Score: 10/20)
- Target: ≥5 questions, ≥3 clarifying (Score: 15/20)
- Excellent: ≥7 questions, ≥5 clarifying, ≥2 insightful (Score: 20/20)

Questions Asked:
$(cat questions.txt)

Timestamp: $(date)
EOF

echo "Results saved to: $RESULTS_FILE"
echo ""

# Cleanup
rm questions.txt

# Exit with appropriate code
if [ $SCORE -ge 10 ]; then
    exit 0  # Pass
else
    exit 1  # Fail
fi

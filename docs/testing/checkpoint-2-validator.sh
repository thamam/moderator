#!/bin/bash
# Checkpoint 2: Discovery Validation
#
# Purpose: Validate that Moderator discovered correct Claude Code data locations
# Pass Criteria: ≥60/100 points
# Score: /100 points
#
# Scoring Breakdown:
#   - Data Location (40 pts): Found .claude/ on all 4 machines
#   - File Format (30 pts): Identified JSONL + JSON formats
#   - Security (20 pts): Flagged .credentials.json risk
#   - Data Size (10 pts): Measured total size
#
# Usage: ./checkpoint-2-validator.sh <discovery-document>

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Input validation
if [ $# -ne 1 ]; then
    echo "Usage: $0 <discovery-document>"
    echo "Example: $0 moderator-discovery-output.md"
    exit 1
fi

DISCOVERY_DOC="$1"
ANSWER_KEY="claude-data-schema.md"

if [ ! -f "$DISCOVERY_DOC" ]; then
    echo "Error: Discovery document not found: $DISCOVERY_DOC"
    exit 1
fi

if [ ! -f "$ANSWER_KEY" ]; then
    echo "Warning: Answer key not found: $ANSWER_KEY"
    echo "Using hardcoded expected values instead."
fi

echo "============================================="
echo "📍 CHECKPOINT 2: Discovery Validation"
echo "============================================="
echo ""

# Initialize score components
DATA_LOCATION_SCORE=0
FILE_FORMAT_SCORE=0
SECURITY_SCORE=0
DATA_SIZE_SCORE=0

# Check 1: Data Location (40 points)
echo "--- Check 1: Data Location (40 pts) ---"
echo "Expected: Found ~/.claude/ on all 4 machines (XPS, ROG, MAC, NELLY)"
echo ""

# Count how many machines were discovered
XPS_FOUND=0
ROG_FOUND=0
MAC_FOUND=0
NELLY_FOUND=0

if grep -qi "xps.*\.claude" "$DISCOVERY_DOC"; then
    echo "✓ XPS: ~/.claude/ found"
    XPS_FOUND=1
else
    echo "✗ XPS: ~/.claude/ NOT found"
fi

if grep -qi "rog.*\.claude" "$DISCOVERY_DOC"; then
    echo "✓ ROG: ~/.claude/ found"
    ROG_FOUND=1
else
    echo "✗ ROG: ~/.claude/ NOT found"
fi

if grep -qi "mac.*\.claude" "$DISCOVERY_DOC"; then
    echo "✓ MAC: ~/.claude/ found"
    MAC_FOUND=1
else
    echo "✗ MAC: ~/.claude/ NOT found"
fi

if grep -qi "nelly.*\.claude" "$DISCOVERY_DOC"; then
    echo "✓ NELLY: ~/.claude/ found"
    NELLY_FOUND=1
else
    echo "✗ NELLY: ~/.claude/ NOT found"
fi

MACHINES_FOUND=$((XPS_FOUND + ROG_FOUND + MAC_FOUND + NELLY_FOUND))

if [ $MACHINES_FOUND -eq 4 ]; then
    DATA_LOCATION_SCORE=40
    echo -e "${GREEN}Score: 40/40${NC}"
elif [ $MACHINES_FOUND -eq 3 ]; then
    DATA_LOCATION_SCORE=30
    echo -e "${YELLOW}Score: 30/40${NC}"
elif [ $MACHINES_FOUND -eq 2 ]; then
    DATA_LOCATION_SCORE=20
    echo -e "${YELLOW}Score: 20/40${NC}"
elif [ $MACHINES_FOUND -eq 1 ]; then
    DATA_LOCATION_SCORE=10
    echo -e "${RED}Score: 10/40${NC}"
else
    DATA_LOCATION_SCORE=0
    echo -e "${RED}Score: 0/40${NC}"
fi

echo ""

# Check 2: File Format (30 points)
echo "--- Check 2: File Format (30 pts) ---"
echo "Expected: Identified JSONL (history.jsonl) and JSON (settings.json)"
echo ""

JSONL_FOUND=0
JSON_FOUND=0

if grep -qi "jsonl\|json lines" "$DISCOVERY_DOC"; then
    echo "✓ JSONL format identified"
    JSONL_FOUND=1
else
    echo "✗ JSONL format NOT identified"
fi

if grep -qi "json.*format\|settings\.json" "$DISCOVERY_DOC"; then
    echo "✓ JSON format identified"
    JSON_FOUND=1
else
    echo "✗ JSON format NOT identified"
fi

if [ $JSONL_FOUND -eq 1 ] && [ $JSON_FOUND -eq 1 ]; then
    FILE_FORMAT_SCORE=30
    echo -e "${GREEN}Score: 30/30${NC}"
elif [ $JSONL_FOUND -eq 1 ] || [ $JSON_FOUND -eq 1 ]; then
    FILE_FORMAT_SCORE=15
    echo -e "${YELLOW}Score: 15/30${NC}"
else
    FILE_FORMAT_SCORE=0
    echo -e "${RED}Score: 0/30${NC}"
fi

echo ""

# Check 3: Security (20 points)
echo "--- Check 3: Security (20 pts) ---"
echo "Expected: Flagged .credentials.json as sensitive"
echo ""

CREDENTIALS_FLAGGED=0
SECURITY_CONCERN=0

if grep -qi "credentials\.json" "$DISCOVERY_DOC"; then
    echo "✓ .credentials.json identified"
    CREDENTIALS_FLAGGED=1

    if grep -qi "sensitive\|security\|exclude\|protect\|secret\|api key" "$DISCOVERY_DOC"; then
        echo "✓ Security concern raised"
        SECURITY_CONCERN=1
    else
        echo "✗ Security concern NOT raised"
    fi
else
    echo "✗ .credentials.json NOT identified"
fi

if [ $CREDENTIALS_FLAGGED -eq 1 ] && [ $SECURITY_CONCERN -eq 1 ]; then
    SECURITY_SCORE=20
    echo -e "${GREEN}Score: 20/20${NC}"
elif [ $CREDENTIALS_FLAGGED -eq 1 ]; then
    SECURITY_SCORE=10
    echo -e "${YELLOW}Score: 10/20${NC}"
else
    SECURITY_SCORE=0
    echo -e "${RED}Score: 0/20${NC}"
fi

echo ""

# Check 4: Data Size (10 points)
echo "--- Check 4: Data Size (10 pts) ---"
echo "Expected: Measured data size on all machines (total ~824MB)"
echo ""

SIZE_MEASURED=0

if grep -qi "MB\|GB\|size\|bytes" "$DISCOVERY_DOC"; then
    echo "✓ Data size measured"
    SIZE_MEASURED=1

    # Bonus: Check if total is approximately correct (600-1000MB range)
    if grep -qiE "(6[0-9]{2}|7[0-9]{2}|8[0-9]{2}|9[0-9]{2}).*MB" "$DISCOVERY_DOC"; then
        echo "✓ Total size approximately correct (~824MB)"
        DATA_SIZE_SCORE=10
    else
        DATA_SIZE_SCORE=7
    fi
else
    echo "✗ Data size NOT measured"
    DATA_SIZE_SCORE=0
fi

if [ $DATA_SIZE_SCORE -eq 10 ]; then
    echo -e "${GREEN}Score: 10/10${NC}"
elif [ $DATA_SIZE_SCORE -gt 0 ]; then
    echo -e "${YELLOW}Score: $DATA_SIZE_SCORE/10${NC}"
else
    echo -e "${RED}Score: 0/10${NC}"
fi

echo ""

# Calculate total score
TOTAL_SCORE=$((DATA_LOCATION_SCORE + FILE_FORMAT_SCORE + SECURITY_SCORE + DATA_SIZE_SCORE))

# Determine status
if [ $TOTAL_SCORE -ge 90 ]; then
    STATUS="${GREEN}✅ EXCELLENT${NC}"
elif [ $TOTAL_SCORE -ge 75 ]; then
    STATUS="${GREEN}✅ PASS (TARGET)${NC}"
elif [ $TOTAL_SCORE -ge 60 ]; then
    STATUS="${YELLOW}⚠️  PASS (MINIMUM)${NC}"
else
    STATUS="${RED}❌ FAIL${NC}"
fi

# Output results
echo "============================================="
echo "CHECKPOINT 2 RESULTS"
echo "============================================="
echo -e "Status: $STATUS"
echo "Score: $TOTAL_SCORE / 100 points"
echo ""
echo "Breakdown:"
echo "  Data Location: $DATA_LOCATION_SCORE / 40 pts (found $MACHINES_FOUND/4 machines)"
echo "  File Format: $FILE_FORMAT_SCORE / 30 pts"
echo "  Security: $SECURITY_SCORE / 20 pts"
echo "  Data Size: $DATA_SIZE_SCORE / 10 pts"
echo ""

# Save results to file
RESULTS_FILE="checkpoint-2-results.txt"
cat > "$RESULTS_FILE" << EOF
Checkpoint 2: Discovery Validation
===================================
Status: $STATUS
Score: $TOTAL_SCORE / 100

Breakdown:
- Data Location: $DATA_LOCATION_SCORE / 40 pts (found $MACHINES_FOUND/4 machines)
  - XPS: $([ $XPS_FOUND -eq 1 ] && echo "✓" || echo "✗")
  - ROG: $([ $ROG_FOUND -eq 1 ] && echo "✓" || echo "✗")
  - MAC: $([ $MAC_FOUND -eq 1 ] && echo "✓" || echo "✗")
  - NELLY: $([ $NELLY_FOUND -eq 1 ] && echo "✓" || echo "✗")

- File Format: $FILE_FORMAT_SCORE / 30 pts
  - JSONL: $([ $JSONL_FOUND -eq 1 ] && echo "✓" || echo "✗")
  - JSON: $([ $JSON_FOUND -eq 1 ] && echo "✓" || echo "✗")

- Security: $SECURITY_SCORE / 20 pts
  - .credentials.json identified: $([ $CREDENTIALS_FLAGGED -eq 1 ] && echo "✓" || echo "✗")
  - Security concern raised: $([ $SECURITY_CONCERN -eq 1 ] && echo "✓" || echo "✗")

- Data Size: $DATA_SIZE_SCORE / 10 pts
  - Size measured: $([ $SIZE_MEASURED -eq 1 ] && echo "✓" || echo "✗")

Pass Criteria:
- Minimum: ≥60/100 points
- Target: ≥75/100 points
- Excellent: ≥90/100 points

Timestamp: $(date)
EOF

echo "Results saved to: $RESULTS_FILE"
echo ""

# Exit with appropriate code
if [ $TOTAL_SCORE -ge 60 ]; then
    exit 0  # Pass
else
    exit 1  # Fail
fi

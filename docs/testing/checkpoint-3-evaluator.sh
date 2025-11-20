#!/bin/bash
# Checkpoint 3: Architecture Quality Evaluator
#
# Purpose: Evaluate architecture document quality using scoring rubric
# Pass Criteria: ≥60/100 points
# Score: /100 points
#
# Scoring Breakdown:
#   - Topology Choice (30 pts): Sound vs flawed architecture
#   - Cross-Platform (25 pts): Addresses Linux/Mac/Windows
#   - Conflict Resolution (25 pts): Has strategy with rationale
#   - Security (20 pts): Credentials, SSH, data protection
#
# Usage: ./checkpoint-3-evaluator.sh <architecture-document>

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Input validation
if [ $# -ne 1 ]; then
    echo "Usage: $0 <architecture-document>"
    echo "Example: $0 moderator-architecture-output.md"
    exit 1
fi

ARCH_DOC="$1"
ANSWER_KEY="claude-sync-architecture.md"

if [ ! -f "$ARCH_DOC" ]; then
    echo "Error: Architecture document not found: $ARCH_DOC"
    exit 1
fi

echo "============================================="
echo "📍 CHECKPOINT 3: Architecture Quality"
echo "============================================="
echo ""
echo "This checkpoint requires human judgment."
echo "Please review the architecture document and score each category."
echo ""

# Initialize score components
TOPOLOGY_SCORE=0
CROSS_PLATFORM_SCORE=0
CONFLICT_RESOLUTION_SCORE=0
SECURITY_SCORE=0

# Check 1: Topology Choice (30 points)
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Category 1: Topology Choice (30 pts)${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo "Review the architecture document and determine:"
echo ""
echo "Question: Is the chosen topology viable for 4 machines?"
echo ""
echo "Options:"
echo "  1) ✅ Yes, sensible choice (hub-and-spoke, peer-to-peer, etc.) [30 pts]"
echo "  2) ⚠️  Workable but suboptimal (unnecessary complexity, single point of failure) [15 pts]"
echo "  3) ❌ Won't scale or has fundamental flaw [0 pts]"
echo ""
read -p "Select (1-3): " topology_choice

case $topology_choice in
    1)
        TOPOLOGY_SCORE=30
        echo -e "${GREEN}Score: 30/30${NC}"
        ;;
    2)
        TOPOLOGY_SCORE=15
        echo -e "${YELLOW}Score: 15/30${NC}"
        ;;
    3)
        TOPOLOGY_SCORE=0
        echo -e "${RED}Score: 0/30${NC}"
        ;;
    *)
        echo "Invalid choice. Defaulting to 0."
        TOPOLOGY_SCORE=0
        ;;
esac

echo ""

# Check 2: Cross-Platform (25 points)
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Category 2: Cross-Platform Support (25 pts)${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo "Review the architecture document and determine:"
echo ""
echo "Question: Does the architecture handle cross-platform differences?"
echo "          (Linux, macOS, Windows)"
echo ""
echo "Options:"
echo "  1) ✅ Explicitly addresses all three platforms (paths, line endings, permissions) [25 pts]"
echo "  2) ⚠️  Mentions cross-platform but lacks detail [15 pts]"
echo "  3) ⚠️  Assumes single platform (Linux-only or Mac-only) [10 pts]"
echo "  4) ❌ Ignores platform differences entirely [0 pts]"
echo ""
read -p "Select (1-4): " platform_choice

case $platform_choice in
    1)
        CROSS_PLATFORM_SCORE=25
        echo -e "${GREEN}Score: 25/25${NC}"
        ;;
    2)
        CROSS_PLATFORM_SCORE=15
        echo -e "${YELLOW}Score: 15/25${NC}"
        ;;
    3)
        CROSS_PLATFORM_SCORE=10
        echo -e "${YELLOW}Score: 10/25${NC}"
        ;;
    4)
        CROSS_PLATFORM_SCORE=0
        echo -e "${RED}Score: 0/25${NC}"
        ;;
    *)
        echo "Invalid choice. Defaulting to 0."
        CROSS_PLATFORM_SCORE=0
        ;;
esac

echo ""

# Check 3: Conflict Resolution (25 points)
echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}Category 3: Conflict Resolution Strategy (25 pts)${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""
echo "Review the architecture document and determine:"
echo ""
echo "Question: Does the architecture have a conflict resolution strategy?"
echo "          (What happens when same file modified on 2+ machines?)"
echo ""
echo "Options:"
echo "  1) ✅ Clear strategy with sound rationale (last-write-wins, merge, prompt) [25 pts]"
echo "  2) ⚠️  Has strategy but unclear or incomplete reasoning [15 pts]"
echo "  3) ⚠️  Acknowledges conflicts but no concrete strategy [5 pts]"
echo "  4) ❌ No mention of conflicts at all [0 pts]"
echo ""
read -p "Select (1-4): " conflict_choice

case $conflict_choice in
    1)
        CONFLICT_RESOLUTION_SCORE=25
        echo -e "${GREEN}Score: 25/25${NC}"
        ;;
    2)
        CONFLICT_RESOLUTION_SCORE=15
        echo -e "${YELLOW}Score: 15/25${NC}"
        ;;
    3)
        CONFLICT_RESOLUTION_SCORE=5
        echo -e "${YELLOW}Score: 5/25${NC}"
        ;;
    4)
        CONFLICT_RESOLUTION_SCORE=0
        echo -e "${RED}Score: 0/25${NC}"
        ;;
    *)
        echo "Invalid choice. Defaulting to 0."
        CONFLICT_RESOLUTION_SCORE=0
        ;;
esac

echo ""

# Check 4: Security (20 points)
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Category 4: Security Considerations (20 pts)${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "Review the architecture document and determine:"
echo ""
echo "Question: Does the architecture address security concerns?"
echo "          (.credentials.json, SSH encryption, data protection)"
echo ""
echo "Options:"
echo "  1) ✅ Comprehensive security (credentials exclusion/encryption, SSH, permissions) [20 pts]"
echo "  2) ⚠️  Identifies .credentials.json risk specifically [15 pts]"
echo "  3) ⚠️  Generic security mention (\"use encryption\") without specifics [10 pts]"
echo "  4) ❌ No security considerations at all [0 pts]"
echo ""
read -p "Select (1-4): " security_choice

case $security_choice in
    1)
        SECURITY_SCORE=20
        echo -e "${GREEN}Score: 20/20${NC}"
        ;;
    2)
        SECURITY_SCORE=15
        echo -e "${GREEN}Score: 15/20${NC}"
        ;;
    3)
        SECURITY_SCORE=10
        echo -e "${YELLOW}Score: 10/20${NC}"
        ;;
    4)
        SECURITY_SCORE=0
        echo -e "${RED}Score: 0/20${NC}"
        ;;
    *)
        echo "Invalid choice. Defaulting to 0."
        SECURITY_SCORE=0
        ;;
esac

echo ""

# Calculate total score
TOTAL_SCORE=$((TOPOLOGY_SCORE + CROSS_PLATFORM_SCORE + CONFLICT_RESOLUTION_SCORE + SECURITY_SCORE))

# Determine status
if [ $TOTAL_SCORE -ge 95 ]; then
    STATUS="${GREEN}✅ EXCELLENT${NC}"
elif [ $TOTAL_SCORE -ge 80 ]; then
    STATUS="${GREEN}✅ PASS (TARGET)${NC}"
elif [ $TOTAL_SCORE -ge 60 ]; then
    STATUS="${YELLOW}⚠️  PASS (MINIMUM)${NC}"
else
    STATUS="${RED}❌ FAIL${NC}"
fi

# Output results
echo "============================================="
echo "CHECKPOINT 3 RESULTS"
echo "============================================="
echo -e "Status: $STATUS"
echo "Score: $TOTAL_SCORE / 100 points"
echo ""
echo "Breakdown:"
echo "  Topology Choice: $TOPOLOGY_SCORE / 30 pts"
echo "  Cross-Platform: $CROSS_PLATFORM_SCORE / 25 pts"
echo "  Conflict Resolution: $CONFLICT_RESOLUTION_SCORE / 25 pts"
echo "  Security: $SECURITY_SCORE / 20 pts"
echo ""

# Save results to file
RESULTS_FILE="checkpoint-3-results.txt"
cat > "$RESULTS_FILE" << EOF
Checkpoint 3: Architecture Quality
===================================
Status: $STATUS
Score: $TOTAL_SCORE / 100

Breakdown:
- Topology Choice: $TOPOLOGY_SCORE / 30 pts
- Cross-Platform Support: $CROSS_PLATFORM_SCORE / 25 pts
- Conflict Resolution Strategy: $CONFLICT_RESOLUTION_SCORE / 25 pts
- Security Considerations: $SECURITY_SCORE / 20 pts

Pass Criteria:
- Minimum: ≥60/100 points
- Target: ≥80/100 points
- Excellent: ≥95/100 points

Architecture Document: $ARCH_DOC
Answer Key: $ANSWER_KEY

Timestamp: $(date)
EOF

echo "Results saved to: $RESULTS_FILE"
echo ""

# Optional: Compare to answer key if available
if [ -f "$ANSWER_KEY" ]; then
    echo "Answer key found: $ANSWER_KEY"
    echo "You may want to compare the Moderator's architecture to the answer key."
    echo ""
fi

# Exit with appropriate code
if [ $TOTAL_SCORE -ge 60 ]; then
    exit 0  # Pass
else
    exit 1  # Fail
fi

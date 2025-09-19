#!/bin/bash
# Analyze requirements coverage against tasks and codebase

DOCS_DIR="./docs"
TASKS_FILE="./docs/TASKS.md"
BACKEND_DIR="./backend"
FRONTEND_DIR="./frontend"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "═══════════════════════════════════════════════════════════"
echo " REQUIREMENTS COVERAGE ANALYSIS"
echo " Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if required files exist
if [ ! -f "$TASKS_FILE" ]; then
    echo -e "${RED}Error: $TASKS_FILE not found!${NC}"
    exit 1
fi

echo "📋 REQUIREMENT DOCUMENTS"
echo "────────────────────────"

# List and check requirement documents
for doc in vision concepts ux technical-architecture database-schema; do
    if [ -f "$DOCS_DIR/$doc.md" ]; then
        echo -e "  ✅ $doc.md found"
    else
        echo -e "  ❌ $doc.md missing"
    fi
done
echo ""

# Extract key requirements from each document
echo "🔍 KEY REQUIREMENTS EXTRACTED"
echo "──────────────────────────────"

# Function to extract section headers from markdown
extract_requirements() {
    local file=$1
    local doc_name=$2

    if [ -f "$file" ]; then
        echo "From $doc_name:"
        # Extract main headers (##) as requirement areas
        grep "^## " "$file" | sed 's/^## /  • /' | head -5
        echo ""
    fi
}

extract_requirements "$DOCS_DIR/vision.md" "vision.md"
extract_requirements "$DOCS_DIR/concepts.md" "concepts.md"
extract_requirements "$DOCS_DIR/ux.md" "ux.md"

# Analyze task coverage
echo "📊 TASK COVERAGE SUMMARY"
echo "────────────────────────"

# Count tasks by status
total_tasks=$(grep -c "^### TASK-" "$TASKS_FILE")
completed=$(grep -c "\[COMPLETED\]" "$TASKS_FILE")
in_progress=$(grep -c "\[IN PROGRESS\]" "$TASKS_FILE")
todo=$(grep -c "\[TODO\]" "$TASKS_FILE")
reviewed=$(grep -c "✅ Reviewed" "$TASKS_FILE")
not_reviewed=$(grep -c "❌ Not Reviewed" "$TASKS_FILE")

echo "Total Tasks:      $total_tasks"
echo "  Completed:      $completed"
echo "  In Progress:    $in_progress"
echo "  Todo:           $todo"
echo ""
echo "Review Status:"
echo "  ✅ Reviewed:     $reviewed"
echo "  ❌ Not Reviewed: $not_reviewed"
echo ""

# Check for implementation artifacts
echo "💻 IMPLEMENTATION STATUS"
echo "────────────────────────"

if [ -d "$BACKEND_DIR" ]; then
    backend_files=$(find "$BACKEND_DIR" -name "*.py" 2>/dev/null | wc -l)
    echo "Backend:  $backend_files Python files"
else
    echo "Backend:  Not initialized"
fi

if [ -d "$FRONTEND_DIR" ]; then
    frontend_files=$(find "$FRONTEND_DIR" -name "*.tsx" -o -name "*.ts" 2>/dev/null | wc -l)
    echo "Frontend: $frontend_files TypeScript files"
else
    echo "Frontend: Not initialized"
fi
echo ""

# Identify potential gaps
echo "⚠️  POTENTIAL GAPS"
echo "──────────────"

# Check for common requirements that might be missing tasks
check_requirement() {
    local keyword=$1
    local description=$2
    local found_in_tasks=$(grep -i "$keyword" "$TASKS_FILE" | wc -l)

    if [ $found_in_tasks -eq 0 ]; then
        echo -e "  ${YELLOW}❌ No tasks for: $description${NC}"
    else
        echo -e "  ${GREEN}✅ $description (found $found_in_tasks references)${NC}"
    fi
}

# Check common requirement areas
check_requirement "authentication\|auth\|login" "User Authentication"
check_requirement "provider\|replicate\|fal" "AI Provider Integration"
check_requirement "database\|schema\|model" "Database Schema"
check_requirement "api\|endpoint\|rest" "API Implementation"
check_requirement "ui\|frontend\|component" "UI Components"
check_requirement "test\|testing\|pytest" "Testing Infrastructure"
check_requirement "docker\|deploy\|container" "Deployment Setup"
check_requirement "websocket\|realtime\|socket" "Real-time Updates"

echo ""

# Check for requirements mentioned in docs but not in tasks
echo "📝 CROSS-REFERENCE CHECK"
echo "────────────────────────"

# Extract unique feature keywords from requirement docs
if [ -f "$DOCS_DIR/concepts.md" ]; then
    echo "Checking concepts.md for uncovered features..."

    # Look for specific entities mentioned in concepts
    for entity in "Product" "Order" "Project" "Collection" "Provider" "Factory"; do
        doc_mentions=$(grep -c "$entity" "$DOCS_DIR/concepts.md" 2>/dev/null || echo 0)
        task_mentions=$(grep -c "$entity" "$TASKS_FILE" 2>/dev/null || echo 0)

        if [ $doc_mentions -gt 0 ]; then
            if [ $task_mentions -eq 0 ]; then
                echo -e "  ${YELLOW}⚠️  '$entity' in docs but not in tasks${NC}"
            else
                echo -e "  ✅ '$entity' covered in tasks"
            fi
        fi
    done
fi

echo ""

# Generate recommendations
echo "💡 RECOMMENDATIONS"
echo "─────────────────"

if [ $not_reviewed -gt 0 ]; then
    echo -e "${YELLOW}1. Review $not_reviewed tasks before implementation${NC}"
fi

if [ $completed -eq 0 ] && [ $total_tasks -gt 0 ]; then
    echo -e "${YELLOW}2. No completed tasks yet - prioritize foundation tasks${NC}"
fi

if [ ! -d "$BACKEND_DIR" ] && [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}3. Project not initialized - run setup tasks first${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Run '/task-coverage-review' for detailed analysis and actions"
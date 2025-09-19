#!/bin/bash
# Generate task status report from TASKS.md

TASKS_FILE="./docs/TASKS.md"

if [ ! -f "$TASKS_FILE" ]; then
    echo "Error: $TASKS_FILE not found!"
    exit 1
fi

echo "═══════════════════════════════════════════════════"
echo " ART FACTORY TASK STATUS REPORT"
echo " Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════"
echo ""

# Count task statuses
echo "TASK SUMMARY"
echo "────────────"
total=$(grep -c "^### TASK-" "$TASKS_FILE")
todo=$(grep -c "\[TODO\]" "$TASKS_FILE")
in_progress=$(grep -c "\[IN PROGRESS\]" "$TASKS_FILE")
review=$(grep -c "\[REVIEW\]" "$TASKS_FILE")
completed=$(grep -c "\[COMPLETED\]" "$TASKS_FILE")
blocked=$(grep -c "\[BLOCKED\]" "$TASKS_FILE")

# Count review statuses
reviewed=$(grep -c "✅ Reviewed" "$TASKS_FILE")
not_reviewed=$(grep -c "❌ Not Reviewed" "$TASKS_FILE")

echo "Total Tasks:    $total"
echo "Todo:           $todo"
echo "In Progress:    $in_progress"
echo "In Review:      $review"
echo "Completed:      $completed"
echo "Blocked:        $blocked"
echo ""
echo "REVIEW STATUS"
echo "─────────────"
echo "✅ Reviewed:     $reviewed"
echo "❌ Not Reviewed: $not_reviewed"
echo ""

# Show in-progress tasks
if [ $in_progress -gt 0 ]; then
    echo "IN PROGRESS TASKS"
    echo "─────────────────"
    grep -A 2 "\[IN PROGRESS\]" "$TASKS_FILE" | grep "^### TASK-" | sed 's/### /  • /'
    echo ""
fi

# Show blocked tasks
if [ $blocked -gt 0 ]; then
    echo "⚠️  BLOCKED TASKS"
    echo "────────────────"
    grep -A 2 "\[BLOCKED\]" "$TASKS_FILE" | grep "^### TASK-" | sed 's/### /  • /'
    echo ""
fi

# Show unreviewed tasks requiring attention
unreviewed_todos=$(grep -B 4 "❌ Not Reviewed" "$TASKS_FILE" | grep "\[TODO\]" | wc -l)
if [ $unreviewed_todos -gt 0 ]; then
    echo "⚠️  TASKS NEEDING REVIEW"
    echo "───────────────────────"
    grep -B 1 "❌ Not Reviewed" "$TASKS_FILE" | grep "^### TASK-" | head -3 | sed 's/### /  • /'
    echo ""
fi

# Show todo tasks (next up)
if [ $todo -gt 0 ]; then
    echo "NEXT UP (Todo Tasks)"
    echo "────────────────────"
    grep "\[TODO\]" "$TASKS_FILE" | head -3 | sed 's/### /  • /'
    echo ""
fi

# Calculate progress
if [ $total -gt 0 ]; then
    progress=$((completed * 100 / total))
    echo "OVERALL PROGRESS"
    echo "────────────────"
    echo -n "["
    
    # Progress bar
    bar_length=30
    filled=$((progress * bar_length / 100))
    for ((i=0; i<filled; i++)); do echo -n "█"; done
    for ((i=filled; i<bar_length; i++)); do echo -n "░"; done
    
    echo "] $progress% ($completed/$total tasks)"
fi

echo ""
echo "═══════════════════════════════════════════════════"
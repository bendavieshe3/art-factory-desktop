# Task List

Show me current active tasks and suggest what to work on next:

## Instructions:

1. Read ./docs/TASKS.md to get all task information

2. Show CURRENT WORK:
   - List any IN PROGRESS tasks with:
     - Task ID and title
     - Completion percentage (based on checklist)
     - Time since started (if tracked)
     - Next checklist items to complete
   - If no tasks in progress, state "No active tasks"

3. Show READY TO START (high priority):
   - List top 5 TODO tasks prioritized by:
     - P0 (Critical) tasks first
     - P1 (High) tasks next
     - Tasks with no dependencies
     - Quick wins (< 2 hour estimates)
   - For each show:
     - Task ID and title
     - Priority level
     - Estimated time
     - Brief description of first steps

4. Show BLOCKED TASKS (if any):
   - List any blocked tasks with:
     - Task ID and title
     - What's blocking it
     - What needs to happen to unblock

5. Provide RECOMMENDATION:
   Based on current state, suggest:
   - If task in progress: Should continue or switch?
   - If no active task: Which specific task to start and why
   - Any tasks that could be done in parallel
   - Quick wins that could build momentum

6. Show RECENT COMPLETIONS (last 3):
   - Task ID and title
   - When completed
   - Key outcomes

Format as a concise, actionable list that helps decide what to work on right now.
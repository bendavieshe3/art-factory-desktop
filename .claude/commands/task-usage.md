# Task Usage Examples

Show common task management operations and practical examples.

## Instructions:

Provide examples of common task operations:

### Starting a New Task
1. Use `/task-create` to add a new task:
   - Provide clear title and description
   - Set appropriate priority (P0-P3)
   - Define acceptance criteria
   - Mark as ❌ Not Reviewed for human review

2. Use `/task-implement TASK-XXX` to begin work:
   - Checks human review status
   - Moves task to IN PROGRESS
   - Shows task details and acceptance criteria

### Working on Tasks
- Keep only 1-2 tasks IN PROGRESS at a time
- Update progress in task descriptions
- Use checklists for complex multi-step tasks
- Reference related files and line numbers

### Completing Tasks
1. Use `/task-completed-review TASK-XXX` when done:
   - Reviews implementation against acceptance criteria
   - Moves to REVIEW status
   - Archives to TASKS-ARCHIVE.md when confirmed complete

### Task Organization
- `/task-prioritize` - Reorder by priority and dependencies
- `/task-status` - Get quick overview of all tasks
- `/task-list` - See what to work on next

### Quality Assurance
- `/task-coverage-review` - Ensure requirements are covered by tasks
- Review acceptance criteria before starting implementation
- Test and verify code before marking tasks complete

### File Locations
- `TASKS.md` - Active tasks
- `TASKS-ARCHIVE.md` - Completed tasks
- `docs/tasks/` - Detailed task specs for complex work
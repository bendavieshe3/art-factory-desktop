# Task Management System Overview

Provide a comprehensive overview of the task management system, its philosophy, and best practices.

## Instructions:

Explain the complete task management system:

### System Philosophy
The task management system is designed to:
- Maintain clear visibility into project progress
- Ensure requirements traceability from docs to implementation
- Require human review before implementation to prevent misunderstandings
- Support both simple tasks and complex multi-phase work
- Archive completed work for reference and learning

### Task Lifecycle
Tasks move through these states:
1. **TODO** - Newly created, needs human review
2. **IN PROGRESS** - Being actively worked on
3. **REVIEW** - Implementation complete, needs verification
4. **COMPLETED** - Verified and archived

### Human Review Workflow
**Critical**: All tasks require human review before implementation
- New tasks always start as ❌ Not Reviewed
- `/task-implement` checks review status and blocks if not reviewed
- Human must confirm task clarity and completeness
- Only mark ✅ Reviewed when confident in task details

### Priority System
- **P0**: Critical/blocking issues
- **P1**: High priority features/fixes
- **P2**: Normal priority work
- **P3**: Nice-to-have/future work

### Task Documentation
- **Simple tasks**: Tracked in TASKS.md with basic details
- **Complex tasks**: Get detailed docs in `docs/tasks/TASK-XXX.md`
- **Acceptance criteria**: Specific, measurable completion requirements
- **Dependencies**: Tracked to ensure proper work ordering

### File Structure
- `TASKS.md` - Active task tracking
- `TASKS-ARCHIVE.md` - Completed tasks archive
- `docs/tasks/` - Detailed task documentation
- `docs/*.md` - Requirements documents (vision, concepts, ux, technical-architecture)
- `scripts/task-report.sh` - Generate task status summary
- `scripts/requirements-coverage.sh` - Analyze requirement coverage

### Requirements Traceability
The system ensures alignment between requirements and implementation:
- Requirements in docs map to specific tasks
- `/task-coverage-review` identifies gaps and inconsistencies
- Tasks reference specific requirement sections
- Implementation includes file:line references

### Best Practices
- Keep 1-2 tasks IN PROGRESS maximum
- Review tasks immediately after creation
- Use specific, measurable acceptance criteria
- Update progress regularly
- Test thoroughly before marking complete
- Reference specific files and line numbers
- Archive completed tasks periodically

### Quality Gates
- Human review required before implementation
- Code quality checks (lint, type check, tests)
- Acceptance criteria verification
- Requirements coverage analysis
- No commits without explicit user request

### Integration with Development
- Tasks guide development priorities
- Implementation references task IDs
- Code quality tools run before task completion
- Testing requirements specified in acceptance criteria
- Documentation updated as part of task completion
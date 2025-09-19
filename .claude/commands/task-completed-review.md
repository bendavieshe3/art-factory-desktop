# Task Review

Review a completed task implementation:

1. Identify the task:
   - Ask for TASK-ID to review
   - Read task details from ./docs/TASKS.md
   - Check implementation notes if available

2. Code review checklist:
   - [ ] All acceptance criteria met
   - [ ] Code follows project conventions (see CLAUDE.md)
   - [ ] Tests written and passing
   - [ ] Documentation updated
   - [ ] No security vulnerabilities
   - [ ] Performance implications considered
   - [ ] Error handling implemented
   - [ ] Logging added where appropriate

3. Technical review:
   - Check adherence to technical-architecture.md
   - Verify database schema matches database-schema.md
   - Ensure testing meets testing-strategy.md standards
   - Validate API contracts if applicable

4. Testing verification:
   - Run unit tests for affected code
   - Check test coverage meets requirements (80%)
   - Verify integration tests if applicable
   - Note any manual testing performed

5. Documentation check:
   - API documentation updated if needed
   - README updated for new features
   - CLAUDE.md updated for new patterns
   - Inline code comments adequate

6. Provide feedback:
   - List what was done well
   - Identify any issues found
   - Suggest improvements if applicable
   - Note any follow-up tasks needed

7. Update task status:
   - If approved: Move to COMPLETED
   - If changes needed: Note required changes, keep IN PROGRESS
   - Update completion date and actual effort

8. Create any follow-up tasks:
   - Technical debt identified
   - Additional features suggested
   - Performance optimizations needed

Provide a clear review summary with actionable feedback.
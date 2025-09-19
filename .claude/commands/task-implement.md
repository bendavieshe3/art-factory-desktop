# Implement Task

Help me implement a specific task from the task list:

1. First, read ./docs/TASKS.md to see available tasks

2. Ask me which task I want to implement (by TASK-ID)

3. Once selected:
   - Read the task details and acceptance criteria
   - **CHECK HUMAN REVIEW STATUS** - Critical step!
     * If **Human Review**: ❌ Not Reviewed:
       - STOP and prompt: "⚠️ This task hasn't been reviewed by a human yet.
         The task details may need elaboration before implementation.
         Would you like to:
         a) Review and elaborate the task together?
         b) Proceed anyway (not recommended)?
         c) Select a different task?"
     * If user chooses to review, help elaborate the task before proceeding
     * Update to ✅ Reviewed once human confirms task is ready
   - Check if there's a detailed implementation file in ./docs/tasks/TASK-XXX-*.md
   - Verify all dependencies are completed
   - Update the task status to "IN PROGRESS" in TASKS.md

4. Begin implementation:
   - Follow the patterns defined in ./docs/technical-architecture.md
   - Adhere to code style guidelines in ./docs/development-workflow.md
   - Write tests as specified in ./docs/testing-strategy.md
   - Update documentation as needed
   - Create feature branch if needed: `git checkout -b feature/task-xxx-description`

5. During implementation:
   - Check off completed acceptance criteria in TASKS.md
   - Add implementation notes to the task
   - Document any important decisions or deviations
   - Commit work regularly with descriptive messages
   - Use `git add -A && git commit -m "Work in progress"` for interim commits

6. Track progress:
   - Regularly update the checklist
   - Note any blockers encountered
   - Keep track of actual time vs estimate

7. When complete:
   - Ensure all acceptance criteria are met
   - Run tests and linting as specified in development-workflow.md
   - Make final commit with task completion message
   - Merge feature branch to main if used
   - Update task status to "REVIEW"
   - Provide summary of what was implemented
   - Update CLAUDE.md with any new patterns or commands learned

Remember to maintain context by referencing CLAUDE.md for project-specific guidelines.
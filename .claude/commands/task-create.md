# Create New Task

Help me create a new task entry in the task tracking system:

1. Gather task information by asking for:
   - Task title/description
   - Priority (P0-Critical, P1-High, P2-Medium, P3-Low)
   - Dependencies on other tasks (if any)
   - GitHub issue number (if exists)

2. Generate acceptance criteria by asking:
   - What are the specific deliverables?
   - What constitutes "done" for this task?
   - Are there any specific technical requirements?
   - What tests should be included?

3. Determine task placement:
   - If it's urgent/immediate: Add to "Todo" section
   - If it's future work: Add to "Backlog" section
   - Check dependencies aren't blocking

4. Create the task entry:
   - Generate next available TASK-XXX ID
   - Add to ./docs/TASKS.md in appropriate section
   - Set **Human Review**: ❌ Not Reviewed (default for new tasks)
   - Use consistent formatting with other tasks

5. **IMPORTANT: Prompt for Human Review**:
   - After creating the task, inform the user:
     "⚠️ This task needs human review before implementation.
      Please review the task details and acceptance criteria.
      Would you like to:
      a) Review and elaborate the task now?
      b) Mark as reviewed (if already sufficient)?
      c) Skip review (not recommended)?"
   - If review requested, help elaborate:
     - Break down complex requirements
     - Add technical specifications
     - Clarify acceptance criteria
     - Note edge cases and considerations
   - Update **Human Review** to ✅ Reviewed once confirmed

6. For complex tasks:
   - Create detailed implementation file: ./docs/tasks/TASK-XXX-{slug}.md
   - Include technical details, approach, and references
   - Add code examples if helpful

7. Update related documentation:
   - If this introduces new patterns, note in CLAUDE.md
   - If this affects architecture, note for technical-architecture.md update

8. Provide confirmation:
   - Show the created task entry
   - Confirm location in task list
   - Remind about any dependencies

Use the existing task format and maintain consistency with current tracking approach.
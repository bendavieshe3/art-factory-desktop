# Task Review Template

## Review Checklist for Task: {TASK_ID}

### 1. Task Clarity
- [ ] Is the task title clear and descriptive?
- [ ] Does the description explain the "why" behind the task?
- [ ] Are success criteria clearly defined?

### 2. Acceptance Criteria
- [ ] Are all acceptance criteria specific and measurable?
- [ ] Do criteria cover both functional and non-functional requirements?
- [ ] Are edge cases and error handling considered?
- [ ] Are testing requirements included?

### 3. Technical Specifications
Consider adding details for:
- [ ] API endpoints and contracts
- [ ] Database schema changes
- [ ] External dependencies
- [ ] Performance requirements
- [ ] Security considerations
- [ ] Backward compatibility

### 4. Implementation Guidance
- [ ] Are there preferred design patterns to follow?
- [ ] Any existing code to reference or extend?
- [ ] Specific libraries or frameworks to use/avoid?
- [ ] Known gotchas or pitfalls to watch for?

### 5. Testing Requirements
- [ ] Unit test coverage expectations
- [ ] Integration test scenarios
- [ ] Manual testing steps
- [ ] Performance benchmarks

### 6. Documentation Needs
- [ ] Code documentation requirements
- [ ] User-facing documentation updates
- [ ] API documentation changes
- [ ] README updates needed

## Elaboration Prompts

### For Complex Features:
1. **Break it down**: Can this task be split into smaller, independent subtasks?
2. **Dependencies**: What other components/services will this interact with?
3. **Data flow**: How will data move through the system?
4. **User journey**: What's the complete user workflow?

### For Bug Fixes:
1. **Root cause**: What's the underlying issue?
2. **Reproduction steps**: How can we consistently reproduce this?
3. **Impact**: What systems/features are affected?
4. **Regression prevention**: How do we prevent this in the future?

### For Infrastructure Tasks:
1. **Current state**: What's the existing setup?
2. **Target state**: What's the desired outcome?
3. **Migration path**: How do we get from A to B safely?
4. **Rollback plan**: How do we revert if needed?

## Review Actions

After reviewing the task with the human:

1. **If task needs elaboration**:
   - Add missing details to task description
   - Expand acceptance criteria
   - Create subtasks if needed
   - Add technical notes section

2. **If task is ready**:
   - Update **Human Review** to ✅ Reviewed
   - Add review timestamp
   - Note any important decisions made during review

3. **If task needs research first**:
   - Mark as blocked
   - Create research task
   - Document what information is needed

## Sample Review Dialog

```
Claude: "I notice this task hasn't been reviewed yet. Let's ensure it's ready for implementation.

Looking at TASK-XXX: [Task Title]

Current acceptance criteria:
• [List current criteria]

Questions to consider:
1. [Specific question about unclear aspect]
2. [Question about technical approach]
3. [Question about testing strategy]

Would you like to:
a) Elaborate on any of these areas?
b) Add additional acceptance criteria?
c) Mark as reviewed if it's already sufficient?
d) Skip review (not recommended)?"
```

## Notes for Claude

When facilitating task review:
- Be specific about what's unclear or missing
- Suggest concrete improvements, not just identify problems
- Consider the project's existing patterns and conventions
- Think about edge cases the human might not have considered
- Ensure testability of the acceptance criteria
- Check that success can be objectively measured
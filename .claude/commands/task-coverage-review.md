# Requirements Review

Analyze task coverage against requirement documents and identify gaps or inconsistencies between requirements, tasks, and implemented code.

## Process:

1. **Scan Requirement Documents**:
   - Read key requirement docs:
     * `./docs/vision.md` - Product vision and goals
     * `./docs/concepts.md` - Domain model and business logic
     * `./docs/ux.md` - UI/UX specifications
     * `./docs/technical-architecture.md` - System design
     * `./docs/database-schema.md` - Data model requirements
   - Extract key features and requirements from each

2. **Analyze Current Tasks**:
   - Read `./docs/TASKS.md` for all tasks (TODO, IN PROGRESS, COMPLETED)
   - Map tasks to requirement areas
   - Identify which requirements have task coverage

3. **Check Implementation Status**:
   - For completed tasks, verify if code exists
   - Check if implementation matches requirements
   - Note any deviations or partial implementations

4. **Generate Coverage Report**:
   ```
   REQUIREMENTS COVERAGE ANALYSIS
   ==============================

   📋 REQUIREMENT AREAS
   --------------------
   ✅ Covered - Has tasks and/or implementation
   ⚠️  Partial - Some tasks but incomplete coverage
   ❌ Missing - No tasks created yet
   🔄 Inconsistent - Conflicts between docs/tasks/code

   [Detailed analysis by requirement area]
   ```

5. **Identify Gaps & Inconsistencies**:

   **Missing Tasks**:
   - Requirements with no corresponding tasks
   - Features mentioned in docs but not tracked

   **Inconsistencies**:
   - Tasks that don't align with requirements
   - Outdated requirements that conflict with current approach
   - Implementation that deviates from specs

   **Over-specification**:
   - Tasks for features not in requirements
   - Implemented features not documented

6. **Recommend Actions**:

   **For Missing Coverage**:
   - Generate new task entries
   - Suggest priority based on dependencies
   - Create acceptance criteria from requirements

   **For Inconsistencies**:
   - Propose requirement doc updates
   - Suggest task modifications
   - Flag implementation issues

   **For Over-specification**:
   - Identify tasks to remove/deprioritize
   - Suggest documentation updates

7. **Update Documentation**:
   After user approval:
   - Add missing tasks to TASKS.md
   - Update requirement docs to resolve inconsistencies
   - Create cross-reference notes between docs and tasks
   - Mark all new tasks as ❌ Not Reviewed

8. **Create Traceability Matrix**:
   Optional detailed mapping:
   ```
   | Requirement | Source Doc | Task ID | Status | Notes |
   |------------|------------|---------|--------|-------|
   | User Auth  | ux.md:45   | TASK-011| TODO   | Needs review |
   | API Design | tech.md:102| TASK-006| TODO   | ❌ Not Reviewed |
   ```

## Key Areas to Check:

### From vision.md:
- Core product goals
- Target user workflows
- Key differentiators
- Success metrics

### From concepts.md:
- Domain entities and relationships
- Business rules and constraints
- Core workflows and processes
- Data model requirements

### From ux.md:
- UI components and layouts
- User interactions and flows
- Navigation structure
- Visual design requirements

### From technical-architecture.md:
- System components
- Integration points
- Technology choices
- Performance requirements
- Security requirements

### From database-schema.md:
- Entity definitions
- Relationships and constraints
- Indexes and optimizations
- Migration requirements

## Output Actions:

1. **Coverage Summary**: High-level overview of requirement coverage
2. **Gap Analysis**: List of uncovered requirements needing tasks
3. **Inconsistency Report**: Conflicts needing resolution
4. **Recommended Tasks**: New tasks to create with priority
5. **Documentation Updates**: Suggested changes to requirement docs
6. **Next Steps**: Prioritized action items

## Notes:
- Focus on functional requirements first
- Consider both explicit and implicit requirements
- Check for requirements that may have been superseded
- Validate that completed tasks actually fulfill their requirements
- Ensure new tasks follow the review workflow (❌ Not Reviewed by default)
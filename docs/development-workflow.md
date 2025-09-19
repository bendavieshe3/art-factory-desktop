# Art Factory Development Workflow

## Project Setup

### Repository Structure
```
art-factory/
├── backend/
│   ├── app/
│   ├── tests/
│   ├── alembic/           # Database migrations
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   ├── public/
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docs/
│   ├── api/              # API documentation
│   ├── architecture/     # Architecture decisions
│   └── guides/           # User/developer guides
├── scripts/
│   ├── setup.sh         # Initial setup script
│   ├── backup.sh        # Backup script
│   └── release.sh       # Release automation
├── storage/             # Default storage location
├── docker-compose.yml
├── .github/
│   └── workflows/       # CI/CD pipelines
├── .env.example
└── README.md
```

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/art-factory.git
cd art-factory

# Run setup script
./scripts/setup.sh

# Or manual setup:
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
alembic upgrade head

# Frontend
cd ../frontend
npm install

# Copy environment file
cp .env.example .env
# Edit .env with your configuration
```

## Development Process

### 1. Issue Tracking

#### Issue Types
- **Feature**: New functionality
- **Bug**: Something isn't working
- **Enhancement**: Improvement to existing functionality
- **Documentation**: Documentation updates
- **Refactor**: Code improvement without functionality change

#### Issue Template
```markdown
## Description
Brief description of the issue

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Technical Notes
Any technical considerations

## Related Issues
- #123
```

#### Issue Workflow
1. **New**: Just created
2. **Triaged**: Reviewed and prioritized
3. **In Progress**: Being worked on
4. **Review**: In code review
5. **Testing**: Being tested
6. **Done**: Completed

### 2. Branch Strategy (Solo Developer)

#### Simplified Branch Types
- `main`: Production-ready code (primary branch)
- `feature/task-xxx-*`: Task-specific work (optional)

#### Naming Convention
```
feature/task-002-backend-setup
feature/task-011-review-architecture
```

#### Why Simplified?
For solo development, complex branching adds overhead without benefit. Use feature branches only for experimental work or when you want to preserve work-in-progress.

### 3. Development Cycle

#### Starting New Work
```bash
# Work directly on main for most tasks
git checkout main
git pull origin main

# Optional: Create feature branch for complex work
git checkout -b feature/task-xxx-description

# Install any new dependencies
cd backend && pip install -r requirements-dev.txt
cd ../frontend && npm install
```

#### During Development
```bash
# Backend development
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend development (separate terminal)
cd frontend
npm run dev

# Run with Docker Compose
docker-compose up
```

#### Code Style
```bash
# Backend
black app/          # Format code
isort app/          # Sort imports
flake8 app/         # Lint code
mypy app/           # Type checking

# Frontend
npm run format      # Format with Prettier
npm run lint        # ESLint
npm run type-check  # TypeScript checking
```

### 4. Testing

```bash
# Backend tests
cd backend
pytest                        # Run all tests
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests
pytest --cov=app            # With coverage

# Frontend tests
cd frontend
npm test                     # Run all tests
npm run test:unit           # Unit tests
npm run test:integration    # Integration tests
npm run test:e2e            # E2E tests
```

### 5. Database Management

#### Creating Migrations
```bash
cd backend
alembic revision --autogenerate -m "Add new table"
# Review generated migration
alembic upgrade head  # Apply migration
```

#### Migration Best Practices
- Always review auto-generated migrations
- Test rollback: `alembic downgrade -1`
- Include both schema and data migrations
- Never edit applied migrations

### 6. Commit Standards

#### Commit Message Format (Simplified)
```
<description>

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

#### Examples
```bash
git commit -m "Add Civitai provider support

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

git commit -m "Fix generation timeout handling

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### Git Aliases (Optional)
Add to ~/.gitconfig:
```
[alias]
    new-task = "!f() { git checkout -b feature/task-$1; }; f"
    task-commit = "!f() { git add -A && git commit -m \"$1\n\n🤖 Generated with Claude Code\n\nCo-Authored-By: Claude <noreply@anthropic.com>\"; }; f"
    wip = "!git add -A && git commit -m \"Work in progress\n\n🤖 Generated with Claude Code\n\nCo-Authored-By: Claude <noreply@anthropic.com>\""
```

### 7. Code Review Process

#### Pull Request Template
```markdown
## Description
What does this PR do?

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

#### Review Checklist
- [ ] Code quality and style
- [ ] Test coverage
- [ ] Performance implications
- [ ] Security considerations
- [ ] Documentation completeness
- [ ] Database migration safety

### 8. Release Process

#### Version Numbering
Follow Semantic Versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

#### Release Steps
```bash
# 1. Create release branch
git checkout -b release/v1.2.0 develop

# 2. Update version numbers
# - backend/app/__version__.py
# - frontend/package.json
# - Update CHANGELOG.md

# 3. Run full test suite
./scripts/run-all-tests.sh

# 4. Build release artifacts
./scripts/build-release.sh

# 5. Merge to main
git checkout main
git merge --no-ff release/v1.2.0
git tag -a v1.2.0 -m "Release version 1.2.0"

# 6. Merge back to develop
git checkout develop
git merge --no-ff release/v1.2.0
```

## Context Retention

### 1. Documentation Standards

#### Code Documentation
```python
# Backend: Use docstrings
def generate_product(
    factory: BaseProductFactory,
    parameters: dict[str, Any]
) -> Product:
    """
    Generate a product using the specified factory.
    
    Args:
        factory: The product factory to use
        parameters: Generation parameters
        
    Returns:
        Generated product instance
        
    Raises:
        ValidationError: If parameters are invalid
        GenerationError: If generation fails
    """
```

```typescript
// Frontend: Use JSDoc
/**
 * Generate a product using the specified parameters
 * @param providerId - The provider to use
 * @param parameters - Generation parameters
 * @returns Promise resolving to the generated product
 */
```

#### Architecture Decision Records (ADR)
Store in `docs/architecture/adr/`
```markdown
# ADR-001: Use FastAPI for Backend

## Status
Accepted

## Context
Need to choose a backend framework...

## Decision
We will use FastAPI because...

## Consequences
Positive: ...
Negative: ...
```

### 2. Knowledge Management

#### CLAUDE.md Updates
- Update after significant architecture changes
- Include new commands and workflows
- Document critical business logic
- Add troubleshooting guides

#### Wiki/Documentation
- Maintain user guides
- API documentation (auto-generated + examples)
- Deployment guides
- Troubleshooting guides

### 3. Development Environment

#### VS Code Settings
`.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### Pre-commit Hooks
`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

## Continuous Integration

### GitHub Actions Workflow
`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm test
```

## Monitoring & Debugging

### Logging Configuration
```python
# backend/app/core/logging.py
import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
```

### Debug Tools
- Backend: FastAPI automatic `/docs` endpoint
- Frontend: React Developer Tools
- Database: SQLite Browser / pgAdmin
- API Testing: Postman/Insomnia collection

## Common Tasks

### Adding a New Provider
1. Create factory class in `backend/app/factories/`
2. Add provider configuration to database
3. Create tests for the factory
4. Update frontend provider selection
5. Document provider-specific parameters

### Adding a New Parameter Type
1. Define in `backend/app/schemas/parameters.py`
2. Add validation in factory base class
3. Create UI component in frontend
4. Add interpolation support if applicable
5. Update documentation

### Performance Optimization
1. Profile with `py-spy` (backend) or Chrome DevTools (frontend)
2. Identify bottlenecks
3. Implement optimization
4. Measure improvement
5. Document in ADR if significant

## Troubleshooting

### Common Issues

#### Database Locked (SQLite)
```bash
# Kill any hanging processes
lsof storage/database.db
kill -9 <PID>
```

#### Port Already in Use
```bash
# Find process using port
lsof -i :8000  # or :3000 for frontend
kill -9 <PID>
```

#### Migration Conflicts
```bash
# Resolve by checking migration history
alembic history
alembic downgrade -1
# Fix conflict
alembic upgrade head
```
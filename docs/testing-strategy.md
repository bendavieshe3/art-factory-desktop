# Art Factory Testing Strategy

## Overview

Comprehensive testing approach covering unit, integration, and end-to-end testing with target coverage of 80% for critical paths.

## Testing Pyramid

```
         /\
        /E2E\        5%  - Critical user journeys
       /______\
      /        \
     /Integration\   25% - API & service integration
    /______________\
   /                \
  /   Unit Tests     \ 70% - Business logic & utilities
 /____________________\
```

## Backend Testing

### 1. Unit Tests

#### Structure
```
backend/tests/unit/
├── test_factories/
│   ├── test_base_factory.py
│   ├── test_replicate_factory.py
│   └── test_parameter_validation.py
├── test_services/
│   ├── test_order_service.py
│   ├── test_generation_service.py
│   └── test_product_service.py
├── test_models/
│   └── test_database_models.py
└── test_utils/
    ├── test_parameter_expansion.py
    └── test_file_handling.py
```

#### Example Unit Test
```python
# tests/unit/test_factories/test_parameter_validation.py
import pytest
from app.factories.base import BaseProductFactory
from app.exceptions import ValidationError

class TestParameterValidation:
    def test_required_parameter_missing(self):
        """Test that missing required parameters raise ValidationError."""
        factory = MockFactory()
        params = {"optional_param": "value"}
        
        with pytest.raises(ValidationError) as exc:
            factory.validate_parameters(params)
        assert "prompt is required" in str(exc.value)
    
    def test_parameter_type_validation(self):
        """Test that incorrect parameter types are rejected."""
        factory = MockFactory()
        params = {
            "prompt": "test",
            "num_steps": "not_a_number"  # Should be int
        }
        
        with pytest.raises(ValidationError) as exc:
            factory.validate_parameters(params)
        assert "num_steps must be an integer" in str(exc.value)
    
    def test_parameter_range_validation(self):
        """Test that out-of-range parameters are rejected."""
        factory = MockFactory()
        params = {
            "prompt": "test",
            "num_steps": 1000  # Max is 100
        }
        
        with pytest.raises(ValidationError) as exc:
            factory.validate_parameters(params)
        assert "num_steps must be between" in str(exc.value)
```

#### Mocking Strategy
```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
def mock_db_session():
    """Provide a mock database session."""
    session = Mock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session

@pytest.fixture
def mock_provider_client():
    """Mock external provider API client."""
    client = Mock()
    client.generate = AsyncMock(return_value={
        "id": "test-123",
        "status": "succeeded",
        "output": ["http://example.com/image.png"]
    })
    return client
```

### 2. Integration Tests

#### Structure
```
backend/tests/integration/
├── test_api/
│   ├── test_orders_api.py
│   ├── test_products_api.py
│   └── test_generation_api.py
├── test_database/
│   ├── test_repositories.py
│   └── test_transactions.py
└── test_providers/
    ├── test_replicate_integration.py
    └── test_fal_integration.py
```

#### Example Integration Test
```python
# tests/integration/test_api/test_orders_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
class TestOrdersAPI:
    async def test_create_order_success(self, client: AsyncClient, test_db):
        """Test successful order creation through API."""
        order_data = {
            "provider": "replicate",
            "model": "stability-ai/sdxl",
            "project_id": "test-project-id",
            "parameters": {
                "prompt": "A beautiful landscape",
                "num_inference_steps": 50
            }
        }
        
        response = await client.post("/api/v1/orders", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["order_id"] is not None
        
        # Verify database state
        order = await test_db.get_order(data["order_id"])
        assert order is not None
        assert order.provider == "replicate"
    
    async def test_parameter_expansion(self, client: AsyncClient):
        """Test that parameter expansion creates multiple items."""
        order_data = {
            "provider": "replicate",
            "model": "stability-ai/sdxl",
            "parameters": {
                "prompt": "A [red,blue,green] car",
                "num_inference_steps": "20,30,40"
            }
        }
        
        response = await client.post("/api/v1/orders", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["total_items"] == 9  # 3 colors × 3 step values
```

#### Database Testing
```python
# tests/integration/test_database/test_repositories.py
import pytest
from app.repositories import OrderRepository, ProductRepository

@pytest.mark.asyncio
class TestOrderRepository:
    async def test_create_and_retrieve_order(self, test_db):
        """Test order creation and retrieval."""
        repo = OrderRepository(test_db)
        
        order = await repo.create({
            "provider": "test",
            "model": "test-model",
            "base_parameter_set": {"prompt": "test"}
        })
        
        retrieved = await repo.get(order.id)
        assert retrieved.id == order.id
        assert retrieved.base_parameter_set["prompt"] == "test"
    
    async def test_update_order_status(self, test_db):
        """Test order status updates."""
        repo = OrderRepository(test_db)
        order = await repo.create({...})
        
        await repo.update_status(order.id, "processing")
        updated = await repo.get(order.id)
        assert updated.status == "processing"
```

### 3. End-to-End Tests

```python
# tests/e2e/test_generation_flow.py
import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_generation_flow():
    """Test complete flow from order to product generation."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Navigate to application
        await page.goto("http://localhost:3000")
        
        # Create new project
        await page.click("text=New Project")
        await page.fill("#project-name", "Test Project")
        await page.click("text=Create")
        
        # Navigate to order page
        await page.click("text=Create Order")
        
        # Fill order form
        await page.select("#provider", "replicate")
        await page.select("#model", "stability-ai/sdxl")
        await page.fill("#prompt", "A test image")
        await page.click("text=Generate")
        
        # Wait for generation to complete
        await page.wait_for_selector(".product-card", timeout=30000)
        
        # Verify product appears
        products = await page.query_selector_all(".product-card")
        assert len(products) > 0
        
        await browser.close()
```

## Frontend Testing

### 1. Component Unit Tests

```typescript
// frontend/src/components/__tests__/OrderForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { OrderForm } from '../OrderForm';
import { mockProvider } from '../../test/mocks';

describe('OrderForm', () => {
  it('validates required fields', async () => {
    render(<OrderForm />);
    
    const submitButton = screen.getByRole('button', { name: /generate/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/prompt is required/i)).toBeInTheDocument();
    });
  });
  
  it('expands token syntax correctly', () => {
    render(<OrderForm />);
    
    const promptInput = screen.getByLabelText(/prompt/i);
    fireEvent.change(promptInput, { 
      target: { value: 'A [red,blue] car' } 
    });
    
    const preview = screen.getByTestId('expansion-preview');
    expect(preview).toHaveTextContent('2 variations');
  });
  
  it('submits order successfully', async () => {
    const onSubmit = jest.fn();
    render(<OrderForm onSubmit={onSubmit} />);
    
    fireEvent.change(screen.getByLabelText(/prompt/i), {
      target: { value: 'Test prompt' }
    });
    fireEvent.click(screen.getByRole('button', { name: /generate/i }));
    
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          parameters: expect.objectContaining({
            prompt: 'Test prompt'
          })
        })
      );
    });
  });
});
```

### 2. Hook Tests

```typescript
// frontend/src/hooks/__tests__/useGeneration.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useGeneration } from '../useGeneration';
import { mockWebSocket } from '../../test/mocks';

describe('useGeneration', () => {
  it('connects to WebSocket on mount', () => {
    const { result } = renderHook(() => 
      useGeneration('order-123')
    );
    
    expect(mockWebSocket.connect).toHaveBeenCalledWith(
      'ws://localhost:8000/ws/generation/order-123'
    );
  });
  
  it('updates progress on message', async () => {
    const { result } = renderHook(() => 
      useGeneration('order-123')
    );
    
    mockWebSocket.simulateMessage({
      type: 'progress',
      completed: 5,
      total: 10
    });
    
    await waitFor(() => {
      expect(result.current.progress).toBe(50);
    });
  });
});
```

### 3. Integration Tests

```typescript
// frontend/src/__tests__/integration/ProjectFlow.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { App } from '../../App';
import { setupMockServer } from '../../test/mockServer';

describe('Project Management Flow', () => {
  beforeAll(() => setupMockServer());
  
  it('creates and manages projects', async () => {
    render(<App />);
    
    // Create project
    fireEvent.click(screen.getByText(/new project/i));
    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: 'Test Project' }
    });
    fireEvent.click(screen.getByText(/create/i));
    
    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });
    
    // Verify project appears in list
    expect(screen.getByTestId('project-card')).toBeInTheDocument();
  });
});
```

## Testing Tools & Configuration

### Backend Tools

#### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

#### Coverage Configuration
```ini
# .coveragerc
[run]
source = app
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

### Frontend Tools

#### jest.config.js
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/test/setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/test/**',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 80,
      statements: 80,
    },
  },
};
```

## Test Data Management

### Fixtures
```python
# tests/fixtures/factories.py
import factory
from app.models import Order, Product

class OrderFactory(factory.Factory):
    class Meta:
        model = Order
    
    provider = "test-provider"
    model = "test-model"
    status = "pending"
    base_parameter_set = factory.LazyFunction(
        lambda: {"prompt": factory.Faker("sentence")}
    )

class ProductFactory(factory.Factory):
    class Meta:
        model = Product
    
    type = "image"
    file_path = factory.Sequence(lambda n: f"/storage/test_{n}.png")
    width = 1024
    height = 1024
```

### Test Database
```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base

@pytest.fixture
async def test_db():
    """Create a test database for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()
```

## Performance Testing

### Load Testing
```python
# tests/performance/test_load.py
import asyncio
import aiohttp
import time

async def test_concurrent_generations():
    """Test system under concurrent load."""
    async def make_request(session, i):
        data = {
            "provider": "test",
            "model": "test-model",
            "parameters": {"prompt": f"Test {i}"}
        }
        async with session.post(
            "http://localhost:8000/api/v1/orders",
            json=data
        ) as response:
            return await response.json()
    
    async with aiohttp.ClientSession() as session:
        start = time.time()
        
        # Create 100 concurrent requests
        tasks = [make_request(session, i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        
        duration = time.time() - start
        
        assert all(r["status"] in ["pending", "processing"] for r in results)
        assert duration < 10  # Should complete within 10 seconds
```

## CI/CD Testing Pipeline

### GitHub Actions Test Workflow
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements-dev.txt
      
      - name: Run backend tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run frontend tests
        run: |
          cd frontend
          npm test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml,./frontend/coverage/lcov.info
```

## Testing Best Practices

### 1. Test Naming
- Use descriptive names: `test_order_creation_with_invalid_parameters_raises_validation_error`
- Group related tests in classes
- Use docstrings to explain complex tests

### 2. Test Independence
- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 3. Mock External Dependencies
- Mock all external API calls
- Use dependency injection for testability
- Create realistic mock responses

### 4. Test Coverage Goals
- 80% overall coverage
- 100% coverage for critical paths
- Focus on behavior, not implementation

### 5. Continuous Testing
- Run tests on every commit
- Fail fast on broken tests
- Regular performance testing

## Testing Checklist

### Before Commit
- [ ] All unit tests pass
- [ ] New code has tests
- [ ] Coverage meets threshold
- [ ] No skipped tests without justification

### Before PR
- [ ] Integration tests pass
- [ ] E2E tests for new features
- [ ] Performance impact assessed
- [ ] Test documentation updated

### Before Release
- [ ] Full test suite passes
- [ ] Manual testing completed
- [ ] Performance benchmarks met
- [ ] Security tests passed
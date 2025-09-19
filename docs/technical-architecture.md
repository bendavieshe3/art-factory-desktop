# Art Factory Technical Architecture

## System Overview

Art Factory is a single-user, locally-deployed application for managing AI-generated media. The architecture prioritizes simplicity, extensibility, and performance for local use while maintaining clean separation of concerns.

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Async Runtime**: asyncio/uvicorn
- **ORM**: SQLAlchemy 2.0 with async support
- **Database**: SQLite (with PostgreSQL-ready abstractions)
- **Task Queue**: Celery with Redis backend (or asyncio tasks for simpler deployment)
- **API Documentation**: OpenAPI/Swagger (auto-generated)

### Frontend
- **Framework**: React 18+ with TypeScript
- **State Management**: Zustand (simpler than Redux)
- **UI Components**: Tailwind CSS + Headless UI
- **Build Tool**: Vite
- **API Client**: Axios with react-query
- **Real-time**: Socket.io-client

### Infrastructure
- **Development**: Docker Compose
- **File Storage**: Local filesystem with configurable base path
- **Caching**: In-memory (with Redis-ready interfaces)
- **Process Manager**: Supervisor or systemd for production

## Architecture Layers

### 1. Presentation Layer (Frontend)

```
src/
├── components/
│   ├── common/          # Shared components
│   ├── projects/        # Project-related components
│   ├── orders/          # Order creation/management
│   ├── inventory/       # Product browsing/management
│   └── admin/           # Settings and configuration
├── hooks/               # Custom React hooks
├── services/            # API client services
├── stores/              # Zustand state stores
├── types/               # TypeScript type definitions
└── utils/               # Utility functions
```

### 2. API Layer (Backend)

```
app/
├── api/
│   ├── v1/
│   │   ├── endpoints/   # REST endpoints
│   │   ├── dependencies/ # Shared dependencies
│   │   └── middleware/   # Custom middleware
├── core/
│   ├── config.py        # Configuration management
│   ├── security.py      # Security utilities
│   └── exceptions.py    # Custom exceptions
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── services/            # Business logic
├── factories/           # Provider factory implementations
└── workers/             # Background task workers
```

### 3. Business Logic Layer

#### Factory Hierarchy
```python
BaseProductFactory (abstract)
├── ReplicateProductFactory
│   ├── ReplicateTxtToImgFactory
│   │   ├── ReplicateFluxFactory
│   │   └── ReplicateSDXLFactory
│   └── ReplicateImgToImgFactory
├── FalProductFactory
│   └── FalTxtToImgFactory
└── LocalProcessingFactory
    └── ImageResizeFactory
```

#### Service Layer
- **OrderService**: Order creation, parameter expansion, generation dispatch
- **GenerationService**: Generation lifecycle management, provider coordination
- **ProductService**: Product creation, file management, metadata extraction
- **ProjectService**: Project CRUD, statistics, featured products
- **ProviderService**: Provider configuration, model discovery, quota management

### 4. Data Layer

#### Database Models
```python
# Core entities
Project
Order
OrderItem
Product
Collection
CollectionProduct

# Supporting entities
Lookup
Template
Tag
TagAssociation

# System entities
Provider
Model
ModelFamily
GenerationLog
```

#### File Storage Structure
```
storage/
├── products/
│   ├── {project_id}/
│   │   ├── {year}/
│   │   │   ├── {month}/
│   │   │   │   └── {product_id}_{hash}.{ext}
├── thumbnails/
│   ├── small/    # 150x150
│   ├── medium/   # 400x400
│   └── large/    # 800x800
├── temp/         # Temporary files during generation
└── exports/      # User exports
```

## Key Design Patterns

### 1. Factory Pattern
- Each provider/model combination has a dedicated factory
- Factories handle parameter validation, API calls, and result processing
- Common functionality inherited from base classes

### 2. Repository Pattern
- Database operations abstracted through repository classes
- Enables easy testing and potential database switching

### 3. Service Layer Pattern
- Business logic separated from API endpoints
- Services coordinate between repositories and external systems

### 4. Observer Pattern
- WebSocket connections for real-time generation updates
- Event-driven architecture for background tasks

## API Design

### RESTful Endpoints

```
# Projects
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{id}
PUT    /api/v1/projects/{id}
DELETE /api/v1/projects/{id}

# Orders
POST   /api/v1/orders
GET    /api/v1/orders
GET    /api/v1/orders/{id}
GET    /api/v1/orders/{id}/items

# Products
GET    /api/v1/products
GET    /api/v1/products/{id}
PUT    /api/v1/products/{id}
DELETE /api/v1/products/{id}
GET    /api/v1/products/{id}/thumbnail

# Providers
GET    /api/v1/providers
GET    /api/v1/providers/{id}/models
POST   /api/v1/providers/{id}/validate

# Generation
POST   /api/v1/generate
GET    /api/v1/generate/{id}/status
POST   /api/v1/generate/{id}/cancel

# WebSocket
WS     /ws/generation/{order_id}
```

### Request/Response Format

```json
// Request
{
  "provider": "replicate",
  "model": "flux-schnell",
  "project_id": "uuid",
  "parameters": {
    "prompt": "A [red,blue] car",
    "num_inference_steps": "4,8",
    "guidance_scale": 3.5
  }
}

// Response
{
  "order_id": "uuid",
  "status": "processing",
  "total_items": 4,
  "completed_items": 0,
  "products": []
}
```

## Security Considerations

### API Security
- Optional JWT authentication for web UI
- API key management with encryption at rest
- Rate limiting per endpoint
- Input validation and sanitization

### File Security
- Virus scanning for imports (optional ClamAV integration)
- File type validation
- Size limits configurable per provider
- Secure file paths (no directory traversal)

## Performance Optimization

### Database
- Strategic indexes on frequently queried fields
- Denormalized counts for performance
- Query optimization with EXPLAIN analysis
- Connection pooling

### Caching
- In-memory cache for provider configurations
- Thumbnail caching with LRU eviction
- Parameter spec caching per factory
- Response caching for read-heavy endpoints

### Async Operations
- Async database queries with SQLAlchemy
- Concurrent provider API calls
- Background task processing
- WebSocket connection pooling

## Monitoring & Logging

### Logging
- Structured logging with Python logging module
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Separate logs for application, generation, and access
- Log rotation with size/time limits

### Metrics
- Generation success/failure rates
- Provider API response times
- Database query performance
- Storage usage trends

## Deployment

### Development Environment
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./storage:/app/storage
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### Production Deployment
- Single binary/installer for Mac OS
- Systemd service for backend
- Nginx for static file serving
- Automated backup scripts

## Extension Points

### Provider Plugins
```python
# Custom provider implementation
class CustomProvider(BaseProductFactory):
    def validate_parameters(self, params: dict) -> dict:
        # Custom validation
        pass
    
    def generate(self, params: dict) -> list[Product]:
        # Custom generation logic
        pass
```

### UI Themes
- CSS variable-based theming
- Dark/light mode support
- Custom color schemes

## Migration Path

### Database Migrations
- Alembic for schema migrations
- Backward-compatible changes
- Migration testing framework

### API Versioning
- URL-based versioning (/api/v1/, /api/v2/)
- Deprecation warnings in headers
- Grace period for version transitions
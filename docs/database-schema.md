# Art Factory Database Schema

## Overview

**Current Implementation**: SQLite database with SQLAlchemy ORM.
**Future Migration Path**: Schema designed for PostgreSQL compatibility.

This document describes the initial implementation using SQLite for development and single-user deployment, with a clear migration path to PostgreSQL for multi-user scenarios.

## SQLite Implementation Notes

- **UUIDs**: Stored as TEXT(36) instead of native UUID type
- **JSON Fields**: Stored as TEXT with JSON serialization/deserialization in Python
- **Timestamps**: Using SQLAlchemy's DateTime with Python datetime objects
- **Foreign Keys**: Enabled via PRAGMA foreign_keys=ON
- **Triggers**: Not implemented initially; denormalized counts managed in Python
- **Full-Text Search**: Deferred to PostgreSQL migration

## Core Tables

### projects
```sql
-- SQLite Implementation
CREATE TABLE projects (
    id TEXT(36) PRIMARY KEY,           -- UUID as string
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active', -- active, archived, completed
    product_count INTEGER DEFAULT 0,     -- denormalized
    order_count INTEGER DEFAULT 0,       -- denormalized
    featured_product_ids_json TEXT,      -- JSON array serialized as TEXT
    settings_json TEXT,                  -- JSON object serialized as TEXT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_at ON projects(created_at);
CREATE INDEX idx_projects_deleted_at ON projects(deleted_at);
```

### orders
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    provider VARCHAR(100) NOT NULL,
    model VARCHAR(200) NOT NULL,
    model_family VARCHAR(100),
    model_modality VARCHAR(100), -- text-to-image, image-to-image, etc.
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, fulfilled, failed, cancelled
    base_parameter_set JSON NOT NULL,  -- user input parameters
    expanded_count INTEGER DEFAULT 0,  -- number of items after expansion
    completed_count INTEGER DEFAULT 0, -- number of completed items
    failed_count INTEGER DEFAULT 0,    -- number of failed items
    template_id UUID REFERENCES templates(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_orders_project_id ON orders(project_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_provider_model ON orders(provider, model);
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

### order_items
```sql
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,  -- order within the batch
    status VARCHAR(50) DEFAULT 'pending', -- pending, generating, complete, failed, cancelled
    generation_parameter_set JSON,     -- expanded parameters for this item
    actual_parameter_set JSON,         -- parameters sent to provider
    return_parameter_set JSON,         -- parameters returned from provider
    provider_request_id VARCHAR(255),  -- provider's ID for tracking
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_status ON order_items(status);
CREATE UNIQUE INDEX idx_order_items_order_sequence ON order_items(order_id, sequence_number);
```

### products
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_item_id UUID REFERENCES order_items(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- image, video, audio
    file_path TEXT NOT NULL,
    file_size BIGINT,
    file_hash VARCHAR(64),  -- SHA256 for deduplication
    thumbnail_paths JSON,    -- {small: path, medium: path, large: path}
    width INTEGER,          -- for images/video
    height INTEGER,         -- for images/video
    duration FLOAT,         -- for video/audio in seconds
    mime_type VARCHAR(100),
    metadata JSON,          -- additional provider-specific metadata
    liked BOOLEAN DEFAULT FALSE,
    rating INTEGER,         -- 1-5 star rating
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_products_project_id ON products(project_id);
CREATE INDEX idx_products_order_item_id ON products(order_item_id);
CREATE INDEX idx_products_type ON products(type);
CREATE INDEX idx_products_liked ON products(liked);
CREATE INDEX idx_products_file_hash ON products(file_hash);
CREATE INDEX idx_products_created_at ON products(created_at);
```

### collections
```sql
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cover_product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    product_count INTEGER DEFAULT 0,  -- denormalized
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_collections_created_at ON collections(created_at);
```

### collection_products
```sql
CREATE TABLE collection_products (
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    position INTEGER DEFAULT 0,  -- for ordering
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id, product_id)
);

CREATE INDEX idx_collection_products_product_id ON collection_products(product_id);
```

## Provider & Model Tables

### providers
```sql
CREATE TABLE providers (
    id VARCHAR(100) PRIMARY KEY,  -- replicate, fal, civitai
    name VARCHAR(255) NOT NULL,
    api_base_url TEXT,
    api_key_encrypted TEXT,        -- encrypted API key
    is_enabled BOOLEAN DEFAULT TRUE,
    rate_limit_requests INTEGER,   -- requests per minute
    rate_limit_tokens INTEGER,     -- tokens per minute
    concurrent_limit INTEGER,      -- max concurrent requests
    settings JSON,                 -- provider-specific settings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### models
```sql
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id VARCHAR(100) NOT NULL REFERENCES providers(id),
    model_id VARCHAR(255) NOT NULL,  -- provider's model identifier
    name VARCHAR(255) NOT NULL,
    family VARCHAR(100),             -- stable-diffusion, flux, midjourney
    modality VARCHAR(100) NOT NULL,  -- text-to-image, image-to-image
    version VARCHAR(50),
    is_available BOOLEAN DEFAULT TRUE,
    parameter_schema JSON,            -- ParameterSpecSet definition
    capabilities JSON,                -- model capabilities/features
    pricing JSON,                     -- cost per generation if applicable
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, model_id)
);

CREATE INDEX idx_models_provider_id ON models(provider_id);
CREATE INDEX idx_models_family ON models(family);
CREATE INDEX idx_models_modality ON models(modality);
```

## Template & Lookup Tables

### templates
```sql
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    provider VARCHAR(100) NOT NULL,
    model VARCHAR(200) NOT NULL,
    parameter_set JSON NOT NULL,  -- saved parameters
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    is_global BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_provider_model ON templates(provider, model);
CREATE INDEX idx_templates_project_id ON templates(project_id);
CREATE INDEX idx_templates_is_global ON templates(is_global);
```

### lookups
```sql
CREATE TABLE lookups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) NOT NULL UNIQUE,
    values JSON NOT NULL,  -- array of values
    description TEXT,
    category VARCHAR(100), -- for grouping in UI
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lookups_key ON lookups(key);
CREATE INDEX idx_lookups_category ON lookups(category);
```

## Tagging System

### tags
```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7),  -- hex color
    description TEXT,
    usage_count INTEGER DEFAULT 0,  -- denormalized
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tags_name ON tags(name);
```

### tag_associations
```sql
CREATE TABLE tag_associations (
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL, -- project, product, collection, order
    entity_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tag_id, entity_type, entity_id)
);

CREATE INDEX idx_tag_associations_entity ON tag_associations(entity_type, entity_id);
```

## System Tables

### generation_logs
```sql
CREATE TABLE generation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_item_id UUID REFERENCES order_items(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20),  -- INFO, WARNING, ERROR
    message TEXT,
    details JSON
);

CREATE INDEX idx_generation_logs_order_item_id ON generation_logs(order_item_id);
CREATE INDEX idx_generation_logs_timestamp ON generation_logs(timestamp);
CREATE INDEX idx_generation_logs_level ON generation_logs(level);
```

### system_settings
```sql
CREATE TABLE system_settings (
    key VARCHAR(255) PRIMARY KEY,
    value JSON NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### migration_history
```sql
CREATE TABLE migration_history (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
```

## Triggers for Denormalized Counts

```sql
-- Update project counts
CREATE TRIGGER update_project_product_count
AFTER INSERT OR DELETE ON products
FOR EACH ROW
EXECUTE FUNCTION update_project_counts();

CREATE TRIGGER update_project_order_count  
AFTER INSERT OR DELETE ON orders
FOR EACH ROW
EXECUTE FUNCTION update_project_counts();

-- Update collection counts
CREATE TRIGGER update_collection_product_count
AFTER INSERT OR DELETE ON collection_products
FOR EACH ROW
EXECUTE FUNCTION update_collection_counts();

-- Update tag usage counts
CREATE TRIGGER update_tag_usage_count
AFTER INSERT OR DELETE ON tag_associations
FOR EACH ROW
EXECUTE FUNCTION update_tag_counts();
```

## Indexes for Performance

### Full-Text Search (PostgreSQL)
```sql
-- For prompt searching
ALTER TABLE orders ADD COLUMN search_vector tsvector;
CREATE INDEX idx_orders_search ON orders USING GIN(search_vector);

-- For product metadata searching  
ALTER TABLE products ADD COLUMN search_vector tsvector;
CREATE INDEX idx_products_search ON products USING GIN(search_vector);
```

### JSON Indexes (PostgreSQL)
```sql
-- For parameter searching
CREATE INDEX idx_orders_parameters ON orders USING GIN(base_parameter_set);
CREATE INDEX idx_products_metadata ON products USING GIN(metadata);
```

## Data Retention & Cleanup

### Soft Deletes
- All main entities have `deleted_at` timestamp
- Queries filter out soft-deleted records by default
- Periodic hard delete after retention period

### Cleanup Jobs
```sql
-- Remove old generation logs
DELETE FROM generation_logs 
WHERE timestamp < NOW() - INTERVAL '30 days';

-- Hard delete soft-deleted records
DELETE FROM products 
WHERE deleted_at < NOW() - INTERVAL '90 days';

-- Clean orphaned files
-- (Handled by application logic comparing filesystem to database)
```

## Current Implementation Status (TASK-102)

### Implemented Models (v1.0)

The following models have been implemented using SQLAlchemy with SQLite:

1. **BaseModel** (Abstract)
   - UUID primary keys as TEXT(36)
   - Soft delete support (deleted_at)
   - Auto-timestamps (created_at, updated_at)
   - JSON field helpers for SQLite
   - Table name auto-generation

2. **Project**
   - Core project management entity
   - JSON fields: featured_product_ids, settings
   - Denormalized counts: product_count, order_count
   - Status management (active/archived/completed)

3. **Order**
   - Generation request container
   - JSON field: base_parameter_set
   - Status tracking and count management
   - Project relationship

4. **OrderItem**
   - Individual API requests (replaces "Generation")
   - JSON fields: generation/actual/return parameter sets
   - Provider tracking and timing
   - Retry and error handling

5. **Product**
   - Generated file outputs
   - JSON fields: thumbnail_paths, extra_metadata
   - File management (hash, size, type)
   - User interaction (liked, rating, notes)

6. **Collection/CollectionProduct**
   - User-defined product groups
   - Many-to-many with position ordering
   - Collection management methods

### Database Management

- **DatabaseManager** class for connection handling
- **Session management** with context managers
- **Foreign key constraints** enabled
- **In-memory testing** support

### Migration Strategy

#### Immediate (SQLite)
- All models ready for production use
- Comprehensive test coverage
- JSON fields work seamlessly

#### Future (PostgreSQL)
- Alembic for schema migrations (TASK-102B)
- Convert JSON TEXT → JSONB columns
- Add full-text search indexes
- Implement database triggers for counts

### Files Created

```
app/models/
├── __init__.py           # Model exports
├── base.py              # BaseModel and helpers
├── project.py           # Project model
├── order.py             # Order and OrderItem models
├── product.py           # Product model
├── collection.py        # Collection models
└── database.py          # Database manager

tests/unit/models/
├── conftest.py          # Test fixtures
├── test_base.py         # BaseModel tests
├── test_project.py      # Project tests
├── test_order.py        # Order/OrderItem tests
├── test_product.py      # Product tests
└── test_collection.py   # Collection tests
```

### Usage Example

```python
from app.models.database import init_database
from app.models import Project, Order, Product

# Initialize database
db_manager = init_database()

# Create models
with db_manager.session_scope() as session:
    project = Project(name="My Project")
    session.add(project)
    session.commit()

    order = Order(
        project_id=project.id,
        provider="replicate",
        model="stability-ai/sdxl",
        base_parameter_set={"prompt": "a red car"}
    )
    session.add(order)
    session.commit()
```
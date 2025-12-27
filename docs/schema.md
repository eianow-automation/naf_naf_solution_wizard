# NAF Solution Wizard JSON Schema

## Overview

The NAF Solution Wizard generates JSON payloads that conform to a specific schema. This schema defines the structure and validation rules for all wizard data.

## Schema Location

The JSON Schema is located at: `schemas/wizard_payload.schema.json`

## Schema Structure

The wizard payload consists of 11 main sections:

### 1. Initiative
Core initiative information including:
- `author` - Name of the person creating the initiative
- `title` - Initiative title (required)
- `description` - Short description/scope (required)
- `category` - Category from predefined list (required)
- `category_other` - Custom category when "Other" is selected
- `problem_statement` - Problem description
- `expected_use` - Expected use cases
- `error_conditions` - Error handling
- `assumptions` - Initiative assumptions
- `deployment_strategy` - Deployment approach
- `deployment_strategy_other` - Custom strategy
- `deployment_strategy_description` - Strategy details
- `out_of_scope` - Items out of scope
- `no_move_forward` - Whether to halt the initiative
- `no_move_forward_reasons` - Reasons for halting

### 2. My Role
User's role information:
- `who` - User role (enum)
- `skills` - Skill level (enum)
- `developer` - Development responsibility (enum)

### 3. Stakeholders
Stakeholder selections:
- `choices` - Stakeholder categories and selections
- `other` - Additional stakeholder information

### 4. Presentation
Presentation layer details:
- `users` - Target users
- `interaction` - Interaction patterns
- `tools` - Presentation tools
- `auth` - Authentication methods

### 5. Intent
Development intent:
- `will_develop` - What will be developed
- `have` - What's already available
- `formats` - Data formats

### 6. Observability
Monitoring and observability:
- `health_signals` - Signals to monitor
- `go_no_go` - Decision criteria
- `tools` - Observability tools
- `add_logic` - Additional logic

### 7. Orchestration
Orchestration information:
- `selections.choice` - Orchestration tool (enum)
- `selections.details` - Implementation details

### 8. Collector
Data collection details:
- `methods` - Collection methods
- `auth` - Authentication
- `normalization` - Data normalization
- `scale` - Scale considerations
- `tools` - Collection tools
- `cadence` - Collection frequency

### 9. Executor
Execution details:
- `methods` - Execution methods
- `change` - Change execution
- `intent` - Intent execution

### 10. Dependencies
External dependencies (array):
- `name` - Dependency name
- `details` - Dependency details

### 11. Timeline
Project timeline:
- `start_date` - Start date (YYYY-MM-DD)
- `total_business_days` - Duration in business days
- `projected_completion` - Completion date
- `build_buy` - Build or buy decision
- `staff_count` - Staff number
- `external_staff_count` - External staff
- `staffing_plan_md` - Staffing plan
- `holiday_region` - Holiday calendar
- `items` - Timeline milestones

## Validation

The schema includes validation rules for:
- Required fields
- Data types
- String lengths
- Enum values
- Date formats
- Array constraints

## Usage

### For Validation
```python
import jsonschema

# Load schema
with open('schemas/wizard_payload.schema.json') as f:
    schema = json.load(f)

# Validate payload
jsonschema.validate(payload, schema)
```

### For IDE Support
Most modern IDEs support JSON Schema for:
- Autocomplete
- Validation
- Documentation on hover
- Error highlighting

## Example

See the `examples` property in the schema for a complete example payload.

## Integration

The schema can be integrated into:
- JSON upload validation in the wizard
- Test data generation
- API documentation
- Type generation (TypeScript, Pydantic, etc.)

## Updates

When adding new fields to the wizard:
1. Update the schema
2. Update this documentation
3. Add validation tests
4. Update examples if needed

## SQL Schema

The wizard payload can be stored in a relational database. Here are SQL statements to create a table for storing wizard data:

### PostgreSQL

```sql
CREATE TABLE wizard_initiatives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Initiative fields
    author VARCHAR(100),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    category_other VARCHAR(100),
    problem_statement TEXT,
    expected_use TEXT,
    error_conditions TEXT,
    assumptions TEXT,
    deployment_strategy VARCHAR(100),
    deployment_strategy_other VARCHAR(100),
    deployment_strategy_description TEXT,
    out_of_scope TEXT,
    no_move_forward VARCHAR(10),
    
    -- My Role fields
    my_role_who VARCHAR(50),
    my_role_skills VARCHAR(20),
    my_role_developer VARCHAR(50),
    
    -- Stakeholders (JSON)
    stakeholders_choices JSONB,
    stakeholders_other TEXT,
    
    -- NAF Components (JSON)
    presentation JSONB,
    intent JSONB,
    observability JSONB,
    orchestration JSONB,
    collector JSONB,
    executor JSONB,
    
    -- Dependencies (JSON array)
    dependencies JSONB,
    
    -- Timeline (JSON)
    timeline JSONB,
    
    -- Full payload (JSON)
    payload JSONB NOT NULL
);

-- Index for common queries
CREATE INDEX idx_wizard_initiatives_title ON wizard_initiatives(title);
CREATE INDEX idx_wizard_initiatives_category ON wizard_initiatives(category);
CREATE INDEX idx_wizard_initiatives_created_at ON wizard_initiatives(created_at);
CREATE INDEX idx_wizard_initiatives_payload_gin ON wizard_initiatives USING gin(payload);
```

### MySQL

```sql
CREATE TABLE wizard_initiatives (
    id BINARY(16) PRIMARY KEY DEFAULT (UUID_TO_BIN(UUID())),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Initiative fields
    author VARCHAR(100),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    category_other VARCHAR(100),
    problem_statement TEXT,
    expected_use TEXT,
    error_conditions TEXT,
    assumptions TEXT,
    deployment_strategy VARCHAR(100),
    deployment_strategy_other VARCHAR(100),
    deployment_strategy_description TEXT,
    out_of_scope TEXT,
    no_move_forward VARCHAR(10),
    
    -- My Role fields
    my_role_who VARCHAR(50),
    my_role_skills VARCHAR(20),
    my_role_developer VARCHAR(50),
    
    -- Stakeholders (JSON)
    stakeholders_choices JSON,
    stakeholders_other TEXT,
    
    -- NAF Components (JSON)
    presentation JSON,
    intent JSON,
    observability JSON,
    orchestration JSON,
    collector JSON,
    executor JSON,
    
    -- Dependencies (JSON array)
    dependencies JSON,
    
    -- Timeline (JSON)
    timeline JSON,
    
    -- Full payload (JSON)
    payload JSON NOT NULL,
    
    INDEX idx_title (title),
    INDEX idx_category (category),
    INDEX idx_created_at (created_at)
);
```

### SQLite

```sql
CREATE TABLE wizard_initiatives (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Initiative fields
    author TEXT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    category_other TEXT,
    problem_statement TEXT,
    expected_use TEXT,
    error_conditions TEXT,
    assumptions TEXT,
    deployment_strategy TEXT,
    deployment_strategy_other TEXT,
    deployment_strategy_description TEXT,
    out_of_scope TEXT,
    no_move_forward TEXT,
    
    -- My Role fields
    my_role_who TEXT,
    my_role_skills TEXT,
    my_role_developer TEXT,
    
    -- Stakeholders (JSON)
    stakeholders_choices TEXT, -- JSON string
    stakeholders_other TEXT,
    
    -- NAF Components (JSON)
    presentation TEXT, -- JSON string
    intent TEXT, -- JSON string
    observability TEXT, -- JSON string
    orchestration TEXT, -- JSON string
    collector TEXT, -- JSON string
    executor TEXT, -- JSON string
    
    -- Dependencies (JSON array)
    dependencies TEXT, -- JSON string
    
    -- Timeline (JSON)
    timeline TEXT, -- JSON string
    
    -- Full payload (JSON)
    payload TEXT NOT NULL -- JSON string
);

-- Triggers for updated_at
CREATE TRIGGER update_wizard_initiatives_updated_at 
    AFTER UPDATE ON wizard_initiatives
    FOR EACH ROW
BEGIN
    UPDATE wizard_initiatives SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

### Notes

1. **UUID Generation**: Each SQL dialect uses its native UUID type or function
2. **JSON Storage**: 
   - PostgreSQL: JSONB for better performance and indexing
   - MySQL 5.7+: JSON type
   - SQLite: TEXT with JSON validation in application code
3. **Indexes**: Added for common query patterns
4. **Timestamps**: Automatic creation and update timestamps
5. **Full Payload**: Stored as JSON for complete data preservation

The schema does not include a UUID field in the wizard payload itself, but the SQL schemas add an `id` field as the primary key for database storage.

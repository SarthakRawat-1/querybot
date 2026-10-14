# QueryBot Local API

FastAPI service for the local QueryBot workspace. It stores conversation history,
dataset metadata, dashboards, and proxies requests to the local data and agent services.

## Features

- 🌐 **Public workspace** - No login or signup is required locally
- 🆔 **UUID Primary Keys** - Uses UUIDs for better security and scalability
- ✅ **Input Validation** - Comprehensive validation using Marshmallow schemas
- 🏗️ **Clean Architecture** - Modular structure with separation of concerns
- 🗄️ **SQLite by default** - Easy local persistence with migrations
- 📝 **Comprehensive Logging** - Structured logging for debugging and monitoring
- 🔄 **CORS Support** - Cross-origin resource sharing for frontend integration

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **Migrations**: Alembic
- **Package Manager**: UV

## Project Structure

```
/project_root
├── app/
│   ├── __init__.py              # Application factory
│   ├── config.py                # Configuration classes (Dev, Prod, Test)
│   ├── extensions.py            # Extension initialization (db, jwt, migrate)
│   ├── models/
│   │   └── user_model.py        # User model with UUID primary key
│   ├── schemas/
│   │   └── user_schema.py       # Marshmallow validation schemas
│   ├── routes/
│   ├── services/
│   └── utils/
│       └── responses.py         # Standardized API responses
├── migrations/                   # Database migration files
├── .env                         # Environment variables
├── main.py                      # Application entry point
├── pyproject.toml              # Project dependencies
└── README.md                   # This file
```

## Setup Instructions

### Prerequisites

- Python 3.12+
- SQLite database (created automatically)
- UV package manager

### Installation

1. **Install dependencies using UV**:
   ```bash
   uv sync
   ```

2. **Set up environment variables**:
   
   The `.env` file should contain:
   ```env
   DATABASE_URL=sqlite:///querybot.db
   SQLITE_SERVICE_URL=http://localhost:3001
   SERVICE_TOKEN=change-me-shared-between-services
   LANGGRAPH_API_URL=http://localhost:8000
   ```

3. **Initialize and run database migrations** (if not already done):
   ```bash
   uv run alembic upgrade head
   ```

4. **Start the development server**:
   ```bash
   uv run python main.py
   ```

The API will be available at `http://127.0.0.1:5000`

## API Endpoints

### Basic Endpoints
- `GET /` - API information
- `GET /health` - Health check

### Public Workspace

The API has no login, signup, token, or session requirement. Dataset uploads,
queries, conversations, and dashboards use one server-managed public workspace.

## Security Features
- **UUID Primary Keys**: Better security than incremental IDs
- **CORS Protection**: Configurable cross-origin policies

## Database Migrations

Common migration commands:

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback to previous migration
uv run alembic downgrade -1
```

## Error Handling

All API responses follow a consistent format:

**Success Response:**
```json
{
  "status": "success",
  "message": "Operation successful",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Error description",
  "errors": {
    "field": ["Specific error messages"]
  }
}
```

## Development

The server runs in debug mode by default for development. Use the following command to start:

```bash
uv run python main.py
```

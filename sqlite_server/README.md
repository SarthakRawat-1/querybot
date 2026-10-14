# QueryBot SQLite Server

A TypeScript Express.js application for handling SQLite database operations with file uploads, query execution, and schema inspection.

## Features

- **TypeScript**: Full TypeScript support with strict type checking
- **Express.js**: Fast and minimalist web framework
- **SQLite Support**: Upload and query SQLite databases
- **CSV Import**: Convert CSV files to SQLite databases automatically
- **File Management**: Automatic cleanup of old uploaded files
- **CORS Support**: Cross-origin resource sharing enabled
- **Error Handling**: Global error handling middleware
- **Request Logging**: Request/response logging

## Project Structure

```
src/
├── controllers/          # Request handlers
│   ├── BaseController.ts # Base controller with error handling
│   └── SqliteController.ts # SQLite operations
├── middleware/          # Express middleware
│   ├── errorHandler.ts  # Global error handling
│   ├── requestLogger.ts # Request logging
│   └── upload.ts        # File upload configuration
├── routes/              # Route definitions
│   ├── index.ts         # Main route aggregator
│   └── sqlite.ts        # SQLite-specific routes
├── types/               # TypeScript type definitions
│   ├── common.ts        # Common interfaces
│   └── sqlite.ts        # SQLite-specific types
├── utils/               # Utility functions
│   └── fileUtils.ts     # File management utilities
├── app.ts               # Express app setup and configuration
└── index.ts             # Application entry point
```

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

1. Clone the repository
2. Navigate to the project directory
3. Install dependencies:

```bash
npm install
```

### Environment Setup

1. Copy the example environment file:

```bash
copy .env.example .env
```

2. Update the `.env` file with your configuration:

```env
PORT=3001
NODE_ENV=development
CORS_ORIGIN=*
MAX_FILE_SIZE=104857600
DB_CLEANUP_INTERVAL=3600000
DB_FILE_RETENTION=14400000
```

### Development

Start the development server with hot reload:

```bash
npm run dev
```

The server will start on `http://localhost:3001`

## API Endpoints

### File Upload

**POST** `/upload-file`
- Upload SQLite database or CSV file
- Supports `.sqlite` and `.csv` file formats
- CSV files are automatically converted to SQLite
- Returns UUID for database identification

**Request:**
```bash
curl -X POST http://localhost:3001/upload-file \
  -F "file=@database.sqlite"
```

**Response:**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Query Execution

**POST** `/execute-query`
- Execute SQL queries on uploaded databases
- Read-only access for security

**Request:**
```bash
curl -X POST http://localhost:3001/execute-query \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "query": "SELECT * FROM users LIMIT 10"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Query executed successfully",
  "data": {
    "results": [
      [1, "John Doe", "john@example.com"],
      [2, "Jane Smith", "jane@example.com"]
    ]
  }
}
```

### Schema Information

**GET** `/get-schema/:uuid`
- Retrieve database schema and sample data
- Shows table structure and example rows

**Request:**
```bash
curl http://localhost:3001/get-schema/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "success": true,
  "message": "Schema retrieved successfully",
  "data": {
    "schema": "Table: users\nCREATE statement: CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)\n\nExample rows:\n{\"id\":1,\"name\":\"John Doe\",\"email\":\"john@example.com\"}\n"
  }
}
```

### System Endpoints

- **GET** `/` - API information and available endpoints
- **GET** `/health` - Health check endpoint

## File Management

### Supported Formats

- **SQLite** (`.sqlite`): Direct upload and use
- **CSV** (`.csv`): Automatically converted to SQLite with table name `csv_data`

### File Retention

- Files older than 4 hours are automatically deleted
- Cleanup runs every hour
- Exception: Files with specific UUID `921c838c-541d-4361-8c96-70cb23abd9f5.sqlite` are preserved

### File Size Limits

- Maximum file size: 100MB
- Configurable via environment variables

## Response Format

All API responses follow this format:

```json
{
  "success": true,
  "message": "Operation description",
  "data": {}, // Response data
  "timestamp": "2023-01-01T00:00:00.000Z"
}
```

Error responses:

```json
{
  "success": false,
  "message": "Error description",
  "data": null,
  "errors": {}, // Additional error details
  "timestamp": "2023-01-01T00:00:00.000Z"
}
```

## Security Features

- Read-only database access for query execution
- File type validation for uploads
- Automatic file cleanup to prevent storage abuse
- CORS configuration for cross-origin requests

## Development Notes

- Uses strict TypeScript configuration for better type safety
- SQLite operations are read-only for security
- File uploads are validated for type and size
- Automatic CSV to SQLite conversion with proper table creation
- Comprehensive error handling and logging

## Available Scripts

- `npm run build` - Compile TypeScript to JavaScript
- `npm run start` - Start the compiled local server
- `npm run dev` - Start the development server with nodemon
- `npm run clean` - Remove compiled JavaScript files

## Contributing

1. Follow the existing code structure and patterns
2. Add proper TypeScript types for all new code
3. Include error handling in all endpoints
4. Update documentation for new features
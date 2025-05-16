# ChatSphere Backend

The backend server for ChatSphere, built with FastAPI and Python 3.12.

## Architecture

- `src/` - Main application source code
  - `api/` - API endpoints and route handlers
  - `models/` - Data models and schemas
  - `services/` - Business logic and services
  - `utils/` - Utility functions and helpers
- `scripts/` - Utility scripts and tools
- `static/` - Static files and assets
- `credentials/` - Secure credential storage (gitignored)

## Key Features

- FastAPI-based REST API
- Firebase Authentication integration
- Vector database for efficient similarity search
- Real-time chat processing
- Custom knowledge base management
- Analytics and diagnostics

## Setup

1. Create a Python virtual environment:
```bash
conda create -n chatsphere python==3.12 -y
conda activate chatsphere
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
- Copy `.env.example` to `.env`
- Update the variables with your credentials

4. Start the development server:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

For detailed API endpoints documentation, see `endpoints.md`.

## Development

- Use `black` for code formatting
- Run tests with `pytest`
- Follow PEP 8 style guidelines

## Dependencies

Key dependencies include:
- FastAPI
- Pydantic
- Firebase Admin
- SQLAlchemy
- Uvicorn
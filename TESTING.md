# Testing Guide

This document describes the testing setup for the AI Learning Platform.

## Overview

The project includes comprehensive test suites for both backend (FastAPI) and frontend (Next.js).

## Backend Tests

### Structure

```
backend/tests/
├── __init__.py
├── conftest.py          # Pytest configuration and fixtures
├── test_auth.py         # Authentication tests
├── test_materials.py    # Materials CRUD tests
├── test_upload.py       # File upload tests
└── test_likes.py        # Like functionality tests
```

### Running Backend Tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/test_auth.py -v

# Run specific test
python -m pytest tests/test_auth.py::TestRegister::test_register_success -v
```

### Test Coverage

The backend tests cover:

1. **Authentication (`test_auth.py`)**
   - User registration (success, duplicate email, validation)
   - User login (success, invalid credentials, inactive user)
   - Token refresh (success, invalid token, expired token)
   - Get current user profile
   - Logout
   - Password hashing

2. **Materials (`test_materials.py`)**
   - List materials with pagination
   - Filter by type (video/pdf)
   - Sort by created_at, view_count, like_count
   - Get material details
   - Delete material (soft delete)
   - CRUD operations

3. **Upload (`test_upload.py`)**
   - Video upload (mp4, webm)
   - PDF upload
   - File validation (type, size)
   - Upload status check
   - Thumbnail status check
   - Delete upload

4. **Likes (`test_likes.py`)**
   - Toggle like/unlike
   - Like count consistency
   - Get like status
   - CRUD operations

### Test Fixtures

The `conftest.py` provides:

- `db_session`: Fresh database session for each test
- `client`: TestClient with database override
- `test_user`: Pre-created test user
- `test_user_2`: Second test user
- `test_user_token`: JWT token for test_user
- `test_video_material`: Pre-created video material
- `test_pdf_material`: Pre-created PDF material
- `test_hidden_material`: Hidden material for access control tests
- `test_processing_material`: Processing status material
- `test_like`: Pre-created like relationship

## Frontend Tests

### Structure

```
frontend/src/components/ui/__tests__/
├── button.test.tsx
└── input.test.tsx
```

### Configuration

- **Jest Config**: `frontend/jest.config.js`
- **Setup File**: `frontend/jest.setup.js`

### Running Frontend Tests

```bash
cd frontend

# Install dependencies first
npm install

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

### Test Coverage

The frontend tests cover:

1. **Button Component**
   - Rendering with different variants (primary, secondary, accent, ghost, outline)
   - Size variations (sm, md, lg)
   - Disabled state
   - Loading state with spinner
   - Click handlers
   - Custom className

2. **Input Component**
   - Rendering with label
   - Placeholder text
   - Error state and messages
   - Helper text
   - Required indicator
   - Disabled state
   - onChange handling
   - Different input types

## CI/CD Integration

### Running All Tests

Use the provided test runner script:

```bash
./run_tests.sh
```

This script:
1. Sets up the Python virtual environment
2. Installs backend dependencies
3. Runs backend tests with coverage
4. Installs frontend dependencies
5. Runs frontend tests with coverage

### Coverage Reports

- **Backend**: `backend/htmlcov/index.html`
- **Frontend**: `frontend/coverage/lcov-report/index.html`

## Test Database

Tests use SQLite in-memory database for:
- Fast execution
- Isolation between tests
- No external dependencies

## Writing New Tests

### Backend Test Example

```python
def test_example(client: TestClient, test_user: User):
    """Test description."""
    response = client.get("/api/v1/some-endpoint")
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

### Frontend Test Example

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../button';

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
```

## Known Issues

1. Some tests check for specific error response formats that may differ from actual API responses. The tests are designed to be flexible but may need adjustment based on the actual error format returned by the API.

2. File upload tests use mocking for MinIO storage to avoid external dependencies.

3. Thumbnail generation tests are mocked since they require ffmpeg and other external tools.

## Dependencies

### Backend Testing
- pytest
- pytest-asyncio
- pytest-cov
- httpx
- bcrypt==4.0.1 (pinned for compatibility)

### Frontend Testing
- jest
- @testing-library/react
- @testing-library/jest-dom
- @testing-library/user-event
- ts-jest
- jest-environment-jsdom

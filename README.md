# YouTube Organizer

## Overview

YouTube Organizer is a full-stack web application designed to help users organize and manage their YouTube playlists more efficiently. The project is also intended as a learning platform for Python and Django, with a focus on best practices and clear explanations throughout the codebase.

## Features

- Organize and manage YouTube playlists
- Google OAuth2 authentication for secure YouTube access
- Modern, responsive frontend UI
- RESTful API backend
- Dockerized for easy local development

## Architecture

This project uses a **monorepo** structure with two main components:

- **Backend** (`backend/`):
  - Python 3, Django, Django REST Framework (DRF)
  - PostgreSQL database
  - Google OAuth2 for YouTube API access
  - All API endpoints and business logic
- **Frontend** (`frontend/`):
  - Next.js (React, TypeScript)
  - Redux Toolkit for state management
  - Communicates with backend via REST API
- **Docker Compose** orchestrates backend, frontend, and database services for local development.

## Tech Stack

- **Backend:** Python, Django, DRF, PostgreSQL
- **Frontend:** Next.js, React, TypeScript, Redux Toolkit
- **DevOps:** Docker, Docker Compose, Makefile

## Getting Started

### Prerequisites

- Docker & Docker Compose installed
- Node.js (for frontend development outside Docker)
- Python 3 (for backend development outside Docker)

### Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/alexisibarra/youtube-organizer.git
   cd youtube-organizer
   ```
2. **Copy environment variables:**
   ```sh
   cp backend/env.template backend/.env
   cp frontend/env.template frontend/.env
   # Fill in required values in both .env files
   ```
3. **Start all services:**

   ```sh
   make up
   ```

   This will build and start the backend, frontend, and database containers.

4. **Run database migrations:**

   ```sh
   make backend-migrate
   ```

5. **Create a Django superuser (optional, for admin access):**

   ```sh
   make backend-createsuperuser
   ```

6. **Access the app:**
   - Frontend: [https://localhost:3000](https://localhost:3000)
   - Backend API: [https://localhost:8000](https://localhost:8000)

### Useful Commands

- `make up` — Start all services
- `make backend-migrate` — Run Django migrations
- `make backend-shell` — Open Django shell
- `make frontend-dev` — Start frontend in development mode

See the `Makefile` for more commands.

## Collaboration

### How to Contribute

1. Fork the repository and create your feature branch:
   ```sh
   git checkout -b feature/your-feature
   ```
2. Make your changes with clear comments and explanations, especially for Python/Django code.
3. Update the `BACKLOG.md` to reflect new features or changes.
4. Run tests and ensure all services work locally.
5. Submit a pull request with a clear description of your changes.

### Guidelines

- Follow best practices for Python, Django, React, and TypeScript.
- Add comments and learning notes, especially when introducing new concepts.
- Keep the codebase clean and organized.
- Use `.env` files for secrets; **never commit credentials**.
- Update documentation as needed.

## Documentation

- See `backend/README.md` and `frontend/README.md` for more details on each part of the stack.
- For OAuth2 setup, refer to `backend/README.md` and `organizer/google_auth_views.py`.

## License

MIT License

---

For questions or help, open an issue or start a discussion in the repository.

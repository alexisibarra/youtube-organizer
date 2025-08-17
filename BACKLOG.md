# YouTube Organizer App Backlog

## Project Goals

- Organize and manage YouTube playlists and videos
- Learn Python and Django through hands-on development

## Features

### Backend (Django + DRF)

- [x] Set up Django project and DRF
      _Django project created, DRF installed, initial app and project structure in place._
- [x] Add .gitignore and ignore **pycache**
      _.gitignore added for Python/Django best practices._
- [x] Run initial migrations
      _Database initialized with Django's default tables._
- [x] Implement OAuth2 authentication with YouTube (Google API)
      _OAuth2 flow implemented in backend, tokens stored securely per user._
- [ ] Endpoints to:
  - [ ] List user playlists (including Watch Later)
  - [ ] Retrieve playlist contents and video metadata
  - [ ] Create, delete, and update playlists
  - [ ] Move, add, and remove videos in playlists
  - [ ] Track and expose YouTube API quota usage
- [ ] Store user tokens securely
- [ ] Unit and integration tests

### Frontend (Next.js + TypeScript + Redux Toolkit)

- [x] Set up Next.js app with TypeScript
      _Next.js app scaffolded with TypeScript for modern React development._
- [x] Install Redux Toolkit and React-Redux
      _State management ready for scalable app structure._
- [ ] Auth flow (Google OAuth2)
- [ ] UI to:
  - [ ] List playlists and show contents
  - [ ] View video metadata
  - [ ] Create, delete, and update playlists
  - [ ] Move, add, and remove videos
  - [ ] Show daily YouTube quota usage
- [ ] Responsive design
- [ ] Error handling and notifications

#### Dynamic User Profile Image in Header

- **Goal:** Display the current logged in user's profile image in the header (YoutubeHeader.tsx).
- **Details:**

      - If the user is authenticated, show their profile picture.
      - If not authenticated, show a default avatar.
      - Requires authentication integration and passing user data to the header.

- **Status:** TODO

#### Notification System in Header

- **Goal:** Decide whether to implement a notification system in the header (YoutubeHeader.tsx).
- **Details:**

      - If notifications are desired, make the notification icon and count dynamic, reflecting real user data.
      - If not, remove the notification section from the header.
      - Requires a product/design decision and, if implemented, backend/user integration.

- **Status:** TODO

### DevOps

- [x] Dockerize backend and frontend
      _Dockerfiles created for both backend (Django) and frontend (Next.js)._
- [x] docker-compose for local development
      _Single command orchestrates backend, frontend, and database. .env files handled._
- [ ] Environment variable management (API keys, secrets)
- [ ] README and setup docs

---

## Learning Goals

- Learn Python basics and Django fundamentals
- Understand REST API design with DRF
- Practice React and Redux Toolkit
- Gain experience with Docker and docker-compose

---

## Progress Tracking

- Check off items as you complete them
- Add notes or questions as you go

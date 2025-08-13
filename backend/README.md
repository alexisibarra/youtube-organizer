# YouTube Organizer Backend

This is a Django project using Django Rest Framework, ready for Dockerization. No frontend or database config is included yet.

## Structure

- `youtube_organizer/` - Django project root
- `organizer/` - Basic app for future endpoints
- `requirements.txt` - Python dependencies

## Setup

1. Create a virtual environment and install requirements:
   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the server:
   ```sh
   python manage.py runserver
   ```

## Google OAuth2 Setup

To enable YouTube authentication, set up a project in Google Cloud Console:

- Enable YouTube Data API v3
- Create OAuth2 credentials (Web application)
- Add the following environment variables (e.g., in your .env file or shell):
  - `GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com`
  - `GOOGLE_CLIENT_SECRET=your_client_secret`
  - `GOOGLE_REDIRECT_URI=http://localhost:8000/oauth2callback/`

## Next Steps

- Add database configuration
- Implement API endpoints in `organizer` app
- Add Docker support

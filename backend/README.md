## Authenticating with Google to Access YouTube Data

To access YouTube data for a user, follow these steps:

1. **Log in to the Django backend:**
   - Go to `/admin/` and log in with your Django user account (or use your frontend login if available).

2. **Start the OAuth2 flow:**
   - While authenticated, visit `/api/auth/google/` in your browser or API client.
   - The response will contain an `auth_url`.

3. **Grant Google permissions:**
   - Open the `auth_url` in your browser.
   - Log in to your Google account and grant the requested permissions.

4. **Callback and token storage:**
   - After granting access, Google will redirect you to `/api/oauth2callback/` on your backend.
   - The backend will securely store your OAuth2 tokens for future API requests.

5. **Access YouTube data:**
   - You can now use endpoints like `/api/youtube/playlists/` to access your YouTube data.

**Note:** You must be logged in as the same Django user for both the OAuth2 flow and YouTube API requests.
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

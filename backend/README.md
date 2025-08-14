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

# Backend Setup: PostgreSQL

This backend is configured to use PostgreSQL.

## Local Development

1. Ensure Docker and Docker Compose are installed.

2. Copy the provided `env.template` file to `.env` and set the required variables:

```
cp env.template .env
```

Edit `.env` and ensure all PostgreSQL and Google OAuth2 variables are set for your environment.

3. Start the services:

```
docker-compose up --build
```

4. Run migrations (in a separate terminal):

```
docker-compose exec backend python manage.py migrate
```

## Notes

- The database data is persisted in a Docker volume (`postgres_data`).
- The Django settings use environment variables for all DB credentials.
- The default user/password is `postgres`/`postgres` for local development.

## Troubleshooting

- If you change the database schema, always re-run migrations.
- If you need to reset the database, remove the `postgres_data` volume:

```
docker-compose down -v
```

---

For any issues, check the logs with:

```
docker-compose logs
```

## Google OAuth2 Setup

To enable YouTube authentication, set up a project in Google Cloud Console:

- Enable YouTube Data API v3
- Create OAuth2 credentials (Web application)
- Add the following environment variables (e.g., in your .env file or shell):
  - `GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com`
  - `GOOGLE_CLIENT_SECRET=your_client_secret`
  - `GOOGLE_REDIRECT_URI=http://localhost:8000/oauth2callback/`

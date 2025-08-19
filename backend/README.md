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
  - `GOOGLE_REDIRECT_URI=https://localhost:8000/api/oauth2callback/`
  - `FRONTEND_AUTH_CALLBACK_URL=https://localhost:3000/auth/callback` # URL to which the backend will redirect after successful OAuth2 login, with the JWT token as a query param

### How FRONTEND_AUTH_CALLBACK_URL Works

After a successful Google OAuth2 login, the backend will generate a JWT for the user and redirect to the URL specified in `FRONTEND_AUTH_CALLBACK_URL`, appending the token as a query parameter:

```
https://localhost:3000/auth/callback?token=YOUR_JWT_TOKEN
```

The frontend should handle this route, extract the token, and store it for future authenticated API requests.

## SSL Certificates for Local Development and Deployment

For OAuth2 and secure cookie handling, the backend must be served over HTTPS, even in local development. This requires SSL certificates:

- **Local development:** Use self-signed certificates (see below).
- **Production/deployment:** Use certificates from a trusted Certificate Authority (e.g., Let's Encrypt).

### Generating Self-Signed Certificates for Local Development

Run the following script from the project root:

```sh
sh generate-dev-cert.sh
```

This will create `localhost.crt` and `localhost.key` in `backend/certs/`. These files are excluded from git for security.

### Deployment Note

- For production, replace the self-signed certs with valid SSL certificates and update your deployment configuration to use them.
- Never commit private keys or certificates to version control.

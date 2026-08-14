
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import os
from google_auth_oauthlib.flow import Flow
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import UserSocialToken
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import requests
from .auth.authentication import COOKIE_NAME
from .auth.tokens import access_lifetime, issue_access_token
from django.shortcuts import redirect

SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'YOUR_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'https://localhost:8000/api/oauth2callback/')

class GoogleAuthInitView(APIView):
    # Explicit, not inherited (AD-14): the user is not logged in yet — this is the
    # login entry point, and it is the one view the default-authenticated policy
    # would otherwise lock.
    permission_classes = [AllowAny]

    def get(self, request):
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
        )
        request.session['oauth_state'] = state
        # google-auth-oauthlib >= 1.x defaults to autogenerate_code_verifier=True, so
        # authorization_url() above sent Google a PKCE code_challenge. The verifier lives only
        # on this Flow instance, which dies with the request — persist it so the callback (a
        # separate request building a separate Flow) can complete the token exchange.
        request.session['oauth_code_verifier'] = flow.code_verifier
        return Response({'auth_url': auth_url})


# This view handles the OAuth2 callback from Google. It does NOT require the user to be authenticated yet.
# Instead, it will:
# 1. Exchange the code for tokens
# 2. Fetch user info from Google
# 3. Find or create a Django user
# 4. Log in the user
# 5. Store the tokens
class GoogleAuthCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # 1. Exchange the code for tokens
        state = request.session.get('oauth_state')
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            state=state,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        # Restore the PKCE verifier stashed by GoogleAuthInitView. Without it Google rejects the
        # exchange with 'invalid_grant: Missing code verifier', because the authorization request
        # carried a code_challenge.
        flow.code_verifier = request.session.get('oauth_code_verifier')
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials

        # 2. Fetch user info from Google using the access token
        userinfo_endpoint = 'https://www.googleapis.com/oauth2/v2/userinfo'
        userinfo_response = requests.get(
            userinfo_endpoint,
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        if userinfo_response.status_code != 200:
            return Response({'error': 'Failed to fetch user info from Google.'}, status=400)
        userinfo = userinfo_response.json()
        email = userinfo.get('email')
        if not email:
            return Response({'error': 'No email found in Google user info.'}, status=400)

        # 3. Find or create a Django user

        # Store profile picture in session for now (or extend User model for persistent storage)
        profile_picture = userinfo.get('picture')
        user, created = User.objects.get_or_create(username=email, defaults={
            'email': email,
            'first_name': userinfo.get('given_name', ''),
            'last_name': userinfo.get('family_name', ''),
        })
        # Save profile picture in session (for demo; for production, extend User model)
        request.session['profile_picture'] = profile_picture

        # 4. Log in the user (creates a session)
        login(request, user)

        # 5. Store the tokens in UserSocialToken
        UserSocialToken.objects.update_or_create(
            user=user,
            defaults={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expiry': credentials.expiry,
                'token_scope': ' '.join(credentials.scopes),
                'token_type': credentials.token_uri,
            }
        )

        # 6. Generate a JWT for the user
        access_token = issue_access_token(user)

        # 7. Set the JWT as an HttpOnly, Secure cookie and redirect to the frontend
        # Learning note: HttpOnly cookies are not accessible via JavaScript, improving security.
        frontend_url = os.environ.get('FRONTEND_AUTH_CALLBACK_URL', 'https://localhost:3000/auth/callback')
        response = redirect(frontend_url)
        # Set the cookie: HttpOnly, Secure, SameSite=None for cross-site usage
        response.set_cookie(
            # The constant, not the literal: this is the mint site and
            # CookieJWTAuthentication is the consumer, so the name has exactly one
            # definition. Changing it breaks every live session.
            key=COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=True,
            samesite='None',
            # Same resolver as the token's own `exp` (AD-14), not a second read of
            # the setting: `access_lifetime()` also applies the default when
            # AUTH_JWT_ACCESS_LIFETIME is absent, so the cookie and the token it
            # carries cannot drift apart even in the case the fallback exists for.
            # Reading `settings.AUTH_JWT_ACCESS_LIFETIME` here would be an
            # AttributeError mid-callback, after the user and Google tokens are saved.
            max_age=int(access_lifetime().total_seconds()),
        )
        return response

class YouTubePlaylistsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            token_obj = UserSocialToken.objects.get(user=user)
        except UserSocialToken.DoesNotExist:
            return Response({'error': 'No YouTube token found for user.'}, status=404)

        credentials_dict = {
            'token': token_obj.access_token,
            'refresh_token': token_obj.refresh_token,
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'scopes': SCOPES,
        }
        credentials = Credentials(**credentials_dict)
        youtube = build('youtube', 'v3', credentials=credentials)
        playlists = youtube.playlists().list(
            part='snippet,contentDetails',
            mine=True,
            maxResults=50
        ).execute()
        return Response(playlists)

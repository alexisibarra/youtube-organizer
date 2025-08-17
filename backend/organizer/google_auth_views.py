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
        user, created = User.objects.get_or_create(username=email, defaults={
            'email': email,
            'first_name': userinfo.get('given_name', ''),
            'last_name': userinfo.get('family_name', ''),
        })

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

        # At this point, the user is authenticated in Django and their tokens are saved.
        return Response({'status': 'User authenticated and token stored successfully', 'email': email})

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

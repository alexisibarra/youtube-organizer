from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import os
from google_auth_oauthlib.flow import Flow
from django.contrib.auth.models import User
from .models import UserSocialToken
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'YOUR_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/oauth2callback/')

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

class GoogleAuthCallbackView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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

        user = request.user
        if not user or not user.is_authenticated:
            return Response({'error': 'User not authenticated.'}, status=401)

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
        return Response({'status': 'Token stored successfully'})

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

from django.urls import path
from .api import views
from .google_auth_views import GoogleAuthInitView, GoogleAuthCallbackView, YouTubePlaylistsView

urlpatterns = [
    # Future endpoints will be added here
    path('auth/google/', GoogleAuthInitView.as_view(), name='google_auth_init'),
    path('oauth2callback/', GoogleAuthCallbackView.as_view(), name='google_auth_callback'),
    path('youtube/playlists/', YouTubePlaylistsView.as_view(), name='youtube_playlists'),
    path('auth/me/', views.MeView.as_view(), name='me'),
]

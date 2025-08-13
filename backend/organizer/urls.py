from django.urls import path
from . import views
from .google_auth_views import GoogleAuthInitView, GoogleAuthCallbackView

urlpatterns = [
    # Future endpoints will be added here
    path('auth/google/', GoogleAuthInitView.as_view(), name='google_auth_init'),
    path('oauth2callback/', GoogleAuthCallbackView.as_view(), name='google_auth_callback'),
]

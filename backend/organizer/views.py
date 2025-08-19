from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# /api/auth/me/ endpoint: returns user info if authenticated, 401 otherwise
class MeView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		user = request.user
		# Try to get profile picture from session (for demo)
		profile_picture = request.session.get('profile_picture')
		return Response({
			'username': user.username,
			'email': user.email,
			'profile_picture': profile_picture,
		})
from django.shortcuts import render

# Create your views here.

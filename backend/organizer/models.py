from django.db import models
from django.contrib.auth.models import User

class UserSocialToken(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	access_token = models.TextField()
	refresh_token = models.TextField()
	token_expiry = models.DateTimeField()
	token_scope = models.TextField(blank=True, null=True)
	token_type = models.CharField(max_length=50, blank=True, null=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Token for {self.user.username}"

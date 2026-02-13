from django.conf import settings
from django.db import models


class GoogleOAuthToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    token_uri = models.CharField(max_length=255, default='https://oauth2.googleapis.com/token')
    client_id = models.TextField()
    client_secret = models.TextField()
    scopes = models.TextField()
    expiry = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'GoogleOAuthToken({self.user_id})'

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    radicale_username = models.CharField(max_length=150)
    radicale_password = models.CharField(max_length=255)
    google_connect_prompted = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.user.username

# Create your models here.

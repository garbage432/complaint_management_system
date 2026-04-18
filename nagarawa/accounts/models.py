from django.contrib.auth.models import AbstractUser
from django.db import models


ROLE_CHOICES = (
    ("user", "User"),
    ("department_admin", "Department Admin"),
    ("super_admin", "Super Admin"),
)


class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=300, blank=True)
    district = models.CharField(max_length=100, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(          # ← now inside the class
        max_length=20,
        choices=ROLE_CHOICES,
        default="user"
    )

    def __str__(self):
        return self.username

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

    @property
    def complaint_count(self):
        return self.complaints.count()

    @property
    def display_name(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username

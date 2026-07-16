from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


ROLE_CHOICES = (
    ("user", _("User")),
    ("department_admin", _("Department Admin")),
    ("super_admin", _("Super Admin")),
)


class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name=_("Avatar"))
    bio = models.TextField(max_length=300, blank=True, verbose_name=_("Bio"))
    district = models.CharField(max_length=100, blank=True, verbose_name=_("District"))
    ward = models.CharField(max_length=100, blank=True, verbose_name=_("Ward"))
    phone = models.CharField(max_length=15, blank=True, verbose_name=_("Phone"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="user",
        verbose_name=_("Role")
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
from django.db import models
from django.conf import settings


class Department(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    icon = models.CharField(
        max_length=50,
        default='🏛️',
        help_text='Emoji icon for the department'
    )

    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text='Hex color for department badge'
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def complaint_count(self):
        """
        Returns number of complaints
        linked to this department.
        Works because Complaint model uses:
        related_name='complaints'
        """
        return self.complaints.count()


class UserProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_department_admin = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.username
from django.db import models
from django.conf import settings
from django.utils.translation import get_language


class Department(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    name_ne = models.CharField(
        max_length=100,
        blank=True,
        help_text='Nepali name of the department (optional)'
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
    def display_name(self):
        """
        Returns the Nepali name if the current active language is Nepali
        and a Nepali name has been set; otherwise falls back to English.
        """
        if get_language() == 'ne' and self.name_ne:
            return self.name_ne
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

    @property
    def role(self):
       if self.user.is_superuser:
          return "superadmin"
       if self.is_department_admin:
          return "deptadmin"
       return "user"
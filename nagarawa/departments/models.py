from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='🏛️', help_text='Emoji icon for the department')
    color = models.CharField(max_length=7, default='#3B82F6', help_text='Hex color for the department badge')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def complaint_count(self):
        return self.complaints.count()

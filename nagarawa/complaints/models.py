from django.db import models
from django.conf import settings
from django.urls import reverse
from departments.models import Department


class Complaint(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_VERIFIED = 'verified'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_SOLVED = 'solved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_SOLVED, 'Solved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    STATUS_COLORS = {
        STATUS_PENDING: '#F59E0B',
        STATUS_VERIFIED: '#3B82F6',
        STATUS_IN_PROGRESS: '#8B5CF6',
        STATUS_SOLVED: '#10B981',
        STATUS_REJECTED: '#EF4444',
    }
    PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('urgent', 'Urgent'),
]


    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='complaints')
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # Location fields
    location_name = models.CharField(max_length=200, blank=True, help_text='Human readable location name')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Engagement
    upvotes = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Vote', related_name='voted_complaints', blank=True)
    view_count = models.PositiveIntegerField(default=0)

    # Admin fields
    admin_note = models.TextField(blank=True, help_text='Internal note from admin (not shown to public)')
    is_anonymous = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('complaints:detail', kwargs={'pk': self.pk})

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self.status, '#6B7280')

    @property
    def vote_score(self):
        up = self.votes.filter(value=1).count()
        down = self.votes.filter(value=-1).count()
        return up - down

    @property
    def upvote_count(self):
        return self.votes.filter(value=1).count()

    @property
    def downvote_count(self):
        return self.votes.filter(value=-1).count()

    @property
    def comment_count(self):
        return self.comments.filter(is_approved=True).count()

    @property
    def has_location(self):
        return self.latitude is not None and self.longitude is not None

    def get_user_vote(self, user):
        if not user.is_authenticated:
            return None
        try:
            return self.votes.get(user=user).value
        except Vote.DoesNotExist:
            return None


class Vote(models.Model):
    UPVOTE = 1
    DOWNVOTE = -1
    VOTE_CHOICES = [(UPVOTE, 'Upvote'), (DOWNVOTE, 'Downvote')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='votes')
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='votes')
    value = models.SmallIntegerField(choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'complaint')

    def __str__(self):
        return f"{self.user} {'up' if self.value == 1 else 'down'}voted {self.complaint}"


class ComplaintImage(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='complaints/images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.complaint.title}"


class StatusLog(models.Model):
    complaint   = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='status_logs')
    changed_by  = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    old_status  = models.CharField(max_length=20)
    new_status  = models.CharField(max_length=20)
    note        = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.complaint} | {self.old_status} → {self.new_status}"


class InternalNote(models.Model):
    complaint  = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='internal_notes')
    author     = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.complaint} by {self.author}"


class ComplaintAssignment(models.Model):
    complaint   = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='assignment')
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='assigned_complaints')
    assigned_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='assignments_made')
    note        = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.complaint} → {self.assigned_to}"


class ComplaintRating(models.Model):
    complaint  = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='rating')
    author     = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    stars      = models.PositiveSmallIntegerField()  # 1-5
    feedback   = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.complaint} — {self.stars}★"


class Notification(models.Model):
    recipient  = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField(max_length=200)
    body       = models.TextField()
    link       = models.CharField(max_length=300, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"→ {self.recipient} | {self.title}"



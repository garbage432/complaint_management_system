from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """A thread between a citizen and a staff member, optionally linked to a complaint."""
    participant_citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='citizen_conversations'
    )
    participant_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_conversations'
    )
    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='conversations'
    )
    subject = models.CharField(max_length=200, blank=True)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conv #{self.pk}: {self.participant_citizen} ↔ {self.participant_staff}"

    def get_other_participant(self, user):
        if user == self.participant_citizen:
            return self.participant_staff
        return self.participant_citizen

    def unread_count_for(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def last_message(self):
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    body = models.TextField(max_length=2000)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Msg from {self.sender} in Conv #{self.conversation_id}"

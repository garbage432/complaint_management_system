from django.contrib import admin
from django.utils.html import format_html
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sender', 'body', 'is_read', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'participant_citizen', 'participant_staff',
        'subject', 'complaint_link', 'message_count',
        'is_closed', 'updated_at'
    ]
    list_filter = ['is_closed', 'created_at']
    search_fields = [
        'participant_citizen__username',
        'participant_staff__username',
        'subject',
        'complaint__title'
    ]
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MessageInline]
    actions = ['close_conversations', 'reopen_conversations']

    def complaint_link(self, obj):
        if obj.complaint:
            return format_html(
                '<a href="/admin/complaints/complaint/{}/change/">{}</a>',
                obj.complaint.pk, obj.complaint.title[:40]
            )
        return '—'
    complaint_link.short_description = 'Complaint'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

    def close_conversations(self, request, queryset):
        queryset.update(is_closed=True)
        self.message_user(request, f'{queryset.count()} conversations closed.')
    close_conversations.short_description = 'Close selected conversations'

    def reopen_conversations(self, request, queryset):
        queryset.update(is_closed=False)
        self.message_user(request, f'{queryset.count()} conversations reopened.')
    reopen_conversations.short_description = 'Reopen selected conversations'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'body_preview', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__username', 'body', 'conversation__subject']
    readonly_fields = ['created_at']

    def body_preview(self, obj):
        return obj.body[:60] + '...' if len(obj.body) > 60 else obj.body
    body_preview.short_description = 'Message'

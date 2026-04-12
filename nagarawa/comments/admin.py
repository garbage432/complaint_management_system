from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'complaint', 'body_preview', 'is_approved', 'is_flagged', 'created_at']
    list_filter = ['is_approved', 'is_flagged', 'created_at']
    search_fields = ['author__username', 'body', 'complaint__title']
    actions = ['approve_comments', 'flag_comments', 'unapprove_comments']
    readonly_fields = ['created_at', 'updated_at']

    def body_preview(self, obj):
        return obj.body[:60] + '...' if len(obj.body) > 60 else obj.body
    body_preview.short_description = 'Comment'

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True, is_flagged=False)
        self.message_user(request, f'{queryset.count()} comments approved.')
    approve_comments.short_description = "Approve selected comments"

    def unapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'{queryset.count()} comments hidden.')
    unapprove_comments.short_description = "Hide selected comments"

    def flag_comments(self, request, queryset):
        queryset.update(is_flagged=True)
        self.message_user(request, f'{queryset.count()} comments flagged.')
    flag_comments.short_description = "Flag selected comments for review"

from django.contrib import admin
from django.utils.html import format_html
from .models import Complaint,Vote, ComplaintImage, StatusLog, InternalNote, ComplaintAssignment, ComplaintRating, Notification

class ComplaintImageInline(admin.TabularInline):
    model = ComplaintImage
    extra = 0
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 60px; border-radius: 4px;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Preview'


class StatusLogInline(admin.TabularInline):
    model = StatusLog
    extra = 0
    readonly_fields = ['changed_by', 'old_status', 'new_status', 'note', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'department', 'status_badge', 'vote_score', 'comment_count', 'view_count', 'created_at']
    list_filter = ['status', 'department', 'is_anonymous', 'created_at']
    search_fields = ['title', 'description', 'author__username', 'location_name']
    readonly_fields = ['view_count', 'created_at', 'updated_at', 'vote_score']
    inlines = [ComplaintImageInline, StatusLogInline]
    actions = ['mark_verified', 'mark_in_progress', 'mark_solved', 'mark_rejected']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Complaint Info', {
            'fields': ('author', 'department', 'title', 'description', 'is_anonymous')
        }),
        ('Location', {
            'fields': ('location_name', 'latitude', 'longitude'),
            'classes': ('collapse',),
        }),
        ('Status Management', {
            'fields': ('status', 'admin_note')
        }),
        ('Metrics', {
            'fields': ('view_count', 'vote_score', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Complaint.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                StatusLog.objects.create(
                    complaint=obj,
                    changed_by=request.user,
                    old_status=old_obj.status,
                    new_status=obj.status,
                    note=obj.admin_note or f'Status updated by {request.user.username}'
                )
        super().save_model(request, obj, form, change)

    def status_badge(self, obj):
        colors = {
            'pending': '#F59E0B',
            'verified': '#3B82F6',
            'in_progress': '#8B5CF6',
            'solved': '#10B981',
            'rejected': '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def _change_status(self, request, queryset, new_status):
        for complaint in queryset:
            old_status = complaint.status
            complaint.status = new_status
            complaint.save()
            StatusLog.objects.create(
                complaint=complaint,
                changed_by=request.user,
                old_status=old_status,
                new_status=new_status,
                note=f'Bulk status update by {request.user.username}'
            )
        self.message_user(request, f'{queryset.count()} complaints updated to {new_status}.')

    def mark_verified(self, request, queryset):
        self._change_status(request, queryset, 'verified')
    mark_verified.short_description = "Mark as Verified"

    def mark_in_progress(self, request, queryset):
        self._change_status(request, queryset, 'in_progress')
    mark_in_progress.short_description = "Mark as In Progress"

    def mark_solved(self, request, queryset):
        self._change_status(request, queryset, 'solved')
    mark_solved.short_description = "Mark as Solved"

    def mark_rejected(self, request, queryset):
        self._change_status(request, queryset, 'rejected')
    mark_rejected.short_description = "Mark as Rejected"


@admin.register(StatusLog)
class StatusLogAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'old_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['new_status', 'created_at']
    search_fields = ['complaint__title', 'changed_by__username']
    readonly_fields = ['complaint', 'changed_by', 'old_status', 'new_status', 'note', 'created_at']





admin.site.register(InternalNote)
admin.site.register(ComplaintAssignment)
admin.site.register(ComplaintRating)
admin.site.register(Notification)

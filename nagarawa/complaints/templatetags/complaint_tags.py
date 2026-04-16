from django import template

register = template.Library()

STATUS_LABELS = {
    'pending': 'Pending',
    'verified': 'Verified',
    'in_progress': 'In Progress',
    'solved': 'Solved',
    'rejected': 'Rejected',
}

@register.filter
def status_label(value):
    return STATUS_LABELS.get(value, value.replace('_', ' ').title())

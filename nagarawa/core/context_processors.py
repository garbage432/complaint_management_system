from departments.models import Department
from complaints.models import Complaint


def global_context(request):
    return {
        'departments': Department.objects.filter(is_active=True),
        'pending_count': Complaint.objects.filter(status='pending').count(),
    }

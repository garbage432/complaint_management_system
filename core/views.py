from django.shortcuts import render, redirect
from complaints.models import Complaint
from departments.models import Department
from django.contrib.auth import get_user_model

User = get_user_model()


def home_view(request):
    if request.user.is_authenticated:
        return redirect('complaints:feed')

    recent = Complaint.objects.select_related('author', 'department').order_by('-created_at')[:6]

    stats = {
        'total_complaints': Complaint.objects.count(),
        'solved': Complaint.objects.filter(status='solved').count(),
        'in_progress': Complaint.objects.filter(status='in_progress').count(),
        'total_users': User.objects.count(),
    }

    departments = Department.objects.filter(is_active=True)

    return render(request, 'core/feed.html', {
        'recent_complaints': recent,
        'stats': stats,
        'departments': departments,
    })


def feed(request):
    return render(request, "complaints/feed.html")
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, ProfileEditForm
from .models import User
from complaints.models import Complaint
from departments.models import UserProfile
from django.db import models

import csv
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Avg
from django.utils import timezone
from complaints.models import (
    Complaint, StatusLog, InternalNote,
    ComplaintAssignment, ComplaintRating, Notification
)
from departments.models import Department, UserProfile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('complaints:feed')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.display_name}! Your account has been created.')
            return redirect('complaints:feed')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})



def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:role_redirect')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # ensure profile exists
            profile, created = UserProfile.objects.get_or_create(user=user)

            # ROLE ROUTING
            if user.is_superuser:
                return redirect('accounts:superadmin_dashboard')

            if profile.is_department_admin:
                return redirect('accounts:deptadmin_dashboard')

            return redirect('accounts:user_dashboard')

        messages.error(request, "Invalid username or password.")

    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})
@login_required
def logout_view(request):
    logout(request)
    return redirect('core:feed')



def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    complaints = profile_user.complaints.select_related('department').order_by('-created_at')[:10]
    return render(request, 'accounts/profile.html', {
        'profile_user': profile_user,
        'complaints': complaints,
    })


@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})

from departments.models import Department

@login_required
def superadmin_dashboard(request):
    complaints = Complaint.objects.all().select_related('department', 'author')
    selected_dept = request.GET.get('dept')
    if selected_dept:
        complaints = complaints.filter(department_id=selected_dept)

    return render(request, "complaints/superadmin.html", {
        "complaints": complaints.order_by('-created_at'),
        "departments": Department.objects.all(),
        "selected_dept": selected_dept,
        "total":            Complaint.objects.count(),
        "pending_count":    Complaint.objects.filter(status='pending').count(),
        "in_progress_count":Complaint.objects.filter(status='in_progress').count(),
        "resolved_count":   Complaint.objects.filter(status='resolved').count(),
        "rejected_count":   Complaint.objects.filter(status='rejected').count(),
    })

@login_required
def deptadmin_dashboard(request):
    profile = request.user.userprofile
    complaints = Complaint.objects.filter(department=profile.department).select_related('author')
    selected_status = request.GET.get('status')
    if selected_status:
        complaints = complaints.filter(status=selected_status)

    base = Complaint.objects.filter(department=profile.department)
    return render(request, "complaints/deptadmin.html", {
        "complaints": complaints.order_by('-created_at'),
        "department": profile.department,
        "selected_status": selected_status,
        "total":            base.count(),
        "pending_count":    base.filter(status='pending').count(),
        "in_progress_count":base.filter(status='in_progress').count(),
        "resolved_count":   base.filter(status='resolved').count(),
    })
from departments.models import Department

@login_required
def user_dashboard(request):
    complaints = Complaint.objects.filter(author=request.user).select_related('department')

    selected_dept = request.GET.get('dept')
    if selected_dept:
        complaints = complaints.filter(department_id=selected_dept)

    return render(request, "complaints/user.html", {
        "complaints": complaints.order_by('-created_at'),
        "departments": Department.objects.all(),
        "selected_dept": selected_dept,
        "pending_count":     Complaint.objects.filter(author=request.user, status='pending').count(),
        "in_progress_count": Complaint.objects.filter(author=request.user, status='in_progress').count(),
        "resolved_count":    Complaint.objects.filter(author=request.user, status='resolved').count(),
    })
@login_required
def role_redirect(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.user.is_superuser:
        return redirect("accounts:superadmin_dashboard")  # ← add accounts:

    if profile.is_department_admin:
        return redirect("accounts:deptadmin_dashboard")   # ← add accounts:

    return redirect("accounts:user_dashboard")     

from django.views.decorators.http import require_POST

@login_required
@require_POST
def update_status(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    # only the dept admin of that complaint's department can update
    profile = request.user.userprofile
    if not (request.user.is_superuser or profile.department == complaint.department):
        messages.error(request, "You don't have permission to update this complaint.")
        return redirect('accounts:deptadmin_dashboard')

    new_status = request.POST.get('status')
    note = request.POST.get('note', '').strip()

    valid = ['pending', 'verified', 'in_progress', 'solved', 'rejected']
    if new_status not in valid:
        messages.error(request, "Invalid status.")
        return redirect('accounts:deptadmin_dashboard')

    old_status = complaint.status
    complaint.status = new_status
    complaint.save()

    # log the change
    if old_status != new_status:
        from complaints.models import StatusLog
        StatusLog.objects.create(
            complaint=complaint,
            changed_by=request.user,
            old_status=old_status,
            new_status=new_status,
            note=note or f"Status changed to {new_status}."
        )
        messages.success(request, f"Complaint marked as {new_status}.")
    else:
        messages.info(request, "Status unchanged.")

    return redirect('accounts:deptadmin_dashboard')


@login_required
def deptadmin_dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    base = Complaint.objects.filter(department=profile.department).select_related('author')

    selected_status = request.GET.get('status')
    complaints = base.filter(status=selected_status) if selected_status else base

    return render(request, "complaints/deptadmin.html", {
        "complaints": complaints.order_by('-created_at').prefetch_related('status_logs'),
        "department": profile.department,
        "selected_status": selected_status,
        "total":            base.count(),
        "pending_count":    base.filter(status='pending').count(),
        "verified_count":   base.filter(status='verified').count(),
        "in_progress_count":base.filter(status='in_progress').count(),
        "solved_count":     base.filter(status='solved').count(),
        "rejected_count":   base.filter(status='rejected').count(),
    })    

# ── helpers ──────────────────────────────────────────────────────────────

def _is_dept_admin(user):
    try:
        return user.userprofile.is_department_admin
    except Exception:
        return False


def _send_notification(recipient, title, body, link=''):
    """Create an in-app notification and send an email."""
    Notification.objects.create(
        recipient=recipient, title=title, body=body, link=link
    )
    if recipient.email:
        send_mail(
            subject=f"[Samparka] {title}",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=True,
        )


# ── dept admin: update status ────────────────────────────────────────────

@login_required
@require_POST
def update_status(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if not (request.user.is_superuser or profile.department == complaint.department):
        messages.error(request, "Permission denied.")
        return redirect('accounts:deptadmin_dashboard')

    new_status = request.POST.get('status')
    note = request.POST.get('note', '').strip()
    valid = ['pending', 'verified', 'in_progress', 'solved', 'rejected']

    if new_status not in valid:
        messages.error(request, "Invalid status.")
        return redirect('accounts:deptadmin_dashboard')

    old_status = complaint.status
    if old_status != new_status:
        complaint.status = new_status
        complaint.save()

        StatusLog.objects.create(
            complaint=complaint,
            changed_by=request.user,
            old_status=old_status,
            new_status=new_status,
            note=note or f"Status updated to {new_status}.",
        )

        # notify the author
        if not complaint.is_anonymous:
            _send_notification(
                recipient=complaint.author,
                title=f"Your complaint status changed to '{new_status}'",
                body=(
                    f"Hi {complaint.author.display_name},\n\n"
                    f"Your complaint '{complaint.title}' has been updated to '{new_status}'.\n"
                    f"Note: {note or 'No additional note.'}\n\n"
                    f"View it at: http://localhost:8000{complaint.get_absolute_url()}"
                ),
                link=complaint.get_absolute_url(),
            )

        messages.success(request, f"Status updated to '{new_status}'.")
    else:
        messages.info(request, "Status unchanged.")

    return redirect('accounts:deptadmin_dashboard')


# ── dept admin: internal note ────────────────────────────────────────────

@login_required
@require_POST
def add_internal_note(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    body = request.POST.get('body', '').strip()

    if not body:
        messages.error(request, "Note cannot be empty.")
        return redirect('accounts:deptadmin_dashboard')

    InternalNote.objects.create(complaint=complaint, author=request.user, body=body)
    messages.success(request, "Internal note added.")
    return redirect('accounts:deptadmin_dashboard')


# ── dept admin: assign staff ─────────────────────────────────────────────

@login_required
@require_POST
def assign_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    staff_id = request.POST.get('staff_id')
    note = request.POST.get('note', '').strip()

    from accounts.models import User as AuthUser
    staff = get_object_or_404(AuthUser, pk=staff_id)

    ComplaintAssignment.objects.update_or_create(
        complaint=complaint,
        defaults={'assigned_to': staff, 'assigned_by': request.user, 'note': note}
    )

    _send_notification(
        recipient=staff,
        title=f"Complaint assigned to you",
        body=(
            f"Hi {staff.display_name},\n\n"
            f"The complaint '{complaint.title}' has been assigned to you.\n"
            f"Note: {note or 'No additional note.'}\n\n"
            f"View it at: http://localhost:8000{complaint.get_absolute_url()}"
        ),
        link=complaint.get_absolute_url(),
    )

    messages.success(request, f"Complaint assigned to {staff.display_name}.")
    return redirect('accounts:deptadmin_dashboard')


# ── dept admin: notify author ────────────────────────────────────────────

@login_required
@require_POST
def notify_author(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    if complaint.is_anonymous:
        messages.error(request, "Cannot notify an anonymous author.")
        return redirect('accounts:deptadmin_dashboard')

    message = request.POST.get('message', '').strip()
    if not message:
        messages.error(request, "Message cannot be empty.")
        return redirect('accounts:deptadmin_dashboard')

    _send_notification(
        recipient=complaint.author,
        title=f"Message from {complaint.department.name} dept.",
        body=(
            f"Hi {complaint.author.display_name},\n\n"
            f"Regarding your complaint '{complaint.title}':\n\n"
            f"{message}\n\n"
            f"View it at: http://localhost:8000{complaint.get_absolute_url()}"
        ),
        link=complaint.get_absolute_url(),
    )

    messages.success(request, "Message sent to author.")
    return redirect('accounts:deptadmin_dashboard')


# ── dept admin: set priority ─────────────────────────────────────────────

@login_required
@require_POST
def set_priority(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    priority = request.POST.get('priority')

    if priority not in ['low', 'medium', 'high', 'urgent']:
        messages.error(request, "Invalid priority.")
        return redirect('accounts:deptadmin_dashboard')

    complaint.priority = priority
    complaint.save()
    messages.success(request, f"Priority set to '{priority}'.")
    return redirect('accounts:deptadmin_dashboard')


# ── dept admin: export CSV ───────────────────────────────────────────────

@login_required
def export_csv(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.user.is_superuser:
        complaints = Complaint.objects.all().select_related('department', 'author')
    elif profile.is_department_admin:
        complaints = Complaint.objects.filter(
            department=profile.department
        ).select_related('department', 'author')
    else:
        messages.error(request, "Permission denied.")
        return redirect('accounts:user_dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="complaints.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Department', 'Author', 'Status', 'Priority', 'Created', 'Due Date', 'Views', 'Vote Score'])

    for c in complaints:
        writer.writerow([
            c.id,
            c.title,
            c.department.name if c.department else '',
            'Anonymous' if c.is_anonymous else c.author.display_name,
            c.status,
            c.priority,
            c.created_at.strftime('%Y-%m-%d'),
            c.due_date or '',
            c.view_count,
            c.vote_score,
        ])

    return response


# ── citizen: rate complaint ──────────────────────────────────────────────

@login_required
@require_POST
def rate_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    if complaint.author != request.user:
        messages.error(request, "You can only rate your own complaints.")
        return redirect(complaint.get_absolute_url())

    if complaint.status != 'solved':
        messages.error(request, "You can only rate solved complaints.")
        return redirect(complaint.get_absolute_url())

    stars = int(request.POST.get('stars', 0))
    feedback = request.POST.get('feedback', '').strip()

    if not 1 <= stars <= 5:
        messages.error(request, "Rating must be between 1 and 5.")
        return redirect(complaint.get_absolute_url())

    ComplaintRating.objects.update_or_create(
        complaint=complaint,
        defaults={'author': request.user, 'stars': stars, 'feedback': feedback}
    )

    messages.success(request, "Thank you for your rating!")
    return redirect(complaint.get_absolute_url())


# ── citizen: withdraw complaint ──────────────────────────────────────────

@login_required
@require_POST
def withdraw_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk, author=request.user)

    if complaint.status != 'pending':
        messages.error(request, "Only pending complaints can be withdrawn.")
        return redirect(complaint.get_absolute_url())

    complaint.delete()
    messages.success(request, "Complaint withdrawn successfully.")
    return redirect('accounts:user_dashboard')


# ── notifications ────────────────────────────────────────────────────────

@login_required
def notifications_view(request):
    # mark as read first
    request.user.notifications.filter(is_read=False).update(is_read=True)
    # then fetch all (now all are read)
    notifications = request.user.notifications.all()
    return render(request, 'accounts/notifications.html', {
        'notifications': notifications,
    })


@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('accounts:notifications')


# ── public stats ─────────────────────────────────────────────────────────

def public_stats(request):
    departments = Department.objects.annotate(
        total=Count('complaints'),
        solved=Count('complaints', filter=models.Q(complaints__status='solved')),
    )

    total       = Complaint.objects.count()
    solved      = Complaint.objects.filter(status='solved').count()
    pending     = Complaint.objects.filter(status='pending').count()
    in_progress = Complaint.objects.filter(status='in_progress').count()
    avg_rating  = ComplaintRating.objects.aggregate(avg=Avg('stars'))['avg'] or 0

    return render(request, 'accounts/public_stats.html', {
        'departments':  departments,
        'total':        total,
        'solved':       solved,
        'pending':      pending,
        'in_progress':  in_progress,
        'avg_rating':   round(avg_rating, 1),
        'solve_rate':   round((solved / total * 100) if total else 0, 1),
    })   # ← add accounts:

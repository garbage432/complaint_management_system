from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Complaint, Vote, ComplaintImage, StatusLog
from .forms import ComplaintForm, ComplaintFilterForm
from comments.models import Comment
from comments.forms import CommentForm
from django.utils import timezone
from django.db import models


def feed_view(request):
    complaints = Complaint.objects.select_related('author', 'department').prefetch_related('votes', 'images', 'comments')

    form = ComplaintFilterForm(request.GET)
    if form.is_valid():
        dept = form.cleaned_data.get('department')
        status = form.cleaned_data.get('status')
        sort = form.cleaned_data.get('sort') or '-created_at'
        q = request.GET.get('q', '').strip()
        if q:
           complaints = complaints.filter(
            models.Q(title__icontains=q) |
            models.Q(description__icontains=q) |
            models.Q(location_name__icontains=q)
    )

        if dept:
            complaints = complaints.filter(department=dept)
        if status:
            complaints = complaints.filter(status=status)
        
    else:
        complaints = complaints.order_by('-created_at')

    paginator = Paginator(complaints, 10)
    page = request.GET.get('page', 1)
    complaints_page = paginator.get_page(page)

    # Attach user vote to each complaint
    if request.user.is_authenticated:
        user_votes = {v.complaint_id: v.value for v in Vote.objects.filter(user=request.user)}
        for c in complaints_page:
            c.user_vote = user_votes.get(c.id)
    
    return render(request, 'complaints/feed.html', {
        'complaints': complaints_page,
        'filter_form': form,
    })


def complaint_detail(request, pk):
    complaint = get_object_or_404(
        Complaint.objects.select_related('author', 'department').prefetch_related('images', 'status_logs__changed_by'),
        pk=pk
    )
    # Increment view count
    complaint.view_count += 1
    complaint.save(update_fields=['view_count'])

    comments = complaint.comments.filter(is_approved=True, parent=None).select_related('author').prefetch_related('replies__author')
    comment_form = CommentForm()
    user_vote = complaint.get_user_vote(request.user)
    today= timezone.now().date(),

    return render(request, 'complaints/detail.html', {
        'complaint': complaint,
        'comments': comments,
        'comment_form': comment_form,
        'user_vote': user_vote,
    })


@login_required
def complaint_create(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.author = request.user
            complaint.save()

            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            for img in images[:5]:  # Max 5 images
                ComplaintImage.objects.create(complaint=complaint, image=img)

            # Create initial status log
            StatusLog.objects.create(
                complaint=complaint,
                changed_by=request.user,
                old_status='',
                new_status='pending',
                note='Complaint submitted'
            )

            messages.success(request, 'Your complaint has been submitted successfully!')
            return redirect('complaints:detail', pk=complaint.pk)
    else:
        form = ComplaintForm()
    return render(request, 'complaints/create.html', {'form': form})


@login_required
def complaint_edit(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk, author=request.user)
    if complaint.status != Complaint.STATUS_PENDING:
        messages.error(request, 'You can only edit pending complaints.')
        return redirect('complaints:detail', pk=pk)

    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES, instance=complaint)
        if form.is_valid():
            form.save()
            messages.success(request, 'Complaint updated.')
            return redirect('complaints:detail', pk=pk)
    else:
        form = ComplaintForm(instance=complaint)
    return render(request, 'complaints/create.html', {'form': form, 'editing': True})


@login_required
def vote_view(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    complaint = get_object_or_404(Complaint, pk=pk)
    value = int(request.POST.get('value', 1))
    if value not in [1, -1]:
        return JsonResponse({'error': 'Invalid vote'}, status=400)

    vote, created = Vote.objects.get_or_create(
        user=request.user,
        complaint=complaint,
        defaults={'value': value}
    )

    if not created:
        if vote.value == value:
            # Toggle off (remove vote)
            vote.delete()
            user_vote = None
        else:
            vote.value = value
            vote.save()
            user_vote = value
    else:
        user_vote = value

    return JsonResponse({
        'score': complaint.vote_score,
        'upvotes': complaint.upvote_count,
        'downvotes': complaint.downvote_count,
        'user_vote': user_vote,
    })


@login_required
def my_complaints(request):
    complaints = request.user.complaints.select_related('department').order_by('-created_at')
    return render(request, 'complaints/my_complaints.html', {'complaints': complaints})

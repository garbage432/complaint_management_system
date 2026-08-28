<<<<<<< HEAD
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from weasyprint import HTML

from .models import Complaint, Vote, ComplaintImage, StatusLog
from .forms import ComplaintForm, ComplaintFilterForm
from comments.models import Comment
from comments.forms import CommentForm

def feed_view(request):
    # Fetch complaints, excluding withdrawn ones from the public feed
    complaints = (
        Complaint.objects
        .select_related('author', 'department')
        .prefetch_related('votes', 'images', 'comments')
        .exclude(status=Complaint.STATUS_WITHDRAWN)
    )

    form = ComplaintFilterForm(request.GET)
    if form.is_valid():
        dept = form.cleaned_data.get('department')
        status = form.cleaned_data.get('status')
        sort = form.cleaned_data.get('sort') or '-created_at'
        q = request.GET.get('q', '').strip()
        
        if q:
            complaints = complaints.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(location_name__icontains=q)
            )

        if dept:
            complaints = complaints.filter(department=dept)
        if status:
            complaints = complaints.filter(status=status)
        
        # Apply sorting dynamic configuration
        complaints = complaints.order_by(sort)
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

    # Trending Threads — Top 3 by vote_score, excluding withdrawn items
    trending_pool = (
        Complaint.objects
        .select_related('author', 'department')
        .prefetch_related('votes')
        .exclude(status=Complaint.STATUS_WITHDRAWN)
    )
    trending_complaints = sorted(trending_pool, key=lambda c: c.vote_score, reverse=True)[:3]

    return render(request, 'complaints/feed.html', {
        'complaints': complaints_page,
        'filter_form': form,
        'trending_complaints': trending_complaints,
    })


def complaint_detail(request, pk):
    # Prevent users from viewing a withdrawn complaint unless they are the author
    complaint = get_object_or_404(
        Complaint.objects.select_related('author', 'department').prefetch_related('images', 'status_logs__changed_by'),
        pk=pk
    )
    
    if complaint.status == Complaint.STATUS_WITHDRAWN and complaint.author != request.user:
        messages.error(request, _('This complaint has been withdrawn and is no longer public.'))
        return redirect('complaints:feed')

    # Increment view count
    complaint.view_count += 1
    complaint.save(update_fields=['view_count'])

    comments = complaint.comments.filter(is_approved=True, parent=None).select_related('author').prefetch_related('replies__author')
    comment_form = CommentForm()
    user_vote = complaint.get_user_vote(request.user)

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

            messages.success(request, _('Your complaint has been submitted successfully!'))
            return redirect('complaints:detail', pk=complaint.pk)
    else:
        form = ComplaintForm()
    return render(request, 'complaints/create.html', {'form': form})


@login_required
def complaint_edit(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk, author=request.user)
    if complaint.status != Complaint.STATUS_PENDING:
        messages.error(request, _('You can only edit pending complaints.'))
        return redirect('complaints:detail', pk=pk)

    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES, instance=complaint)
        if form.is_valid():
            form.save()
            messages.success(request, _('Complaint updated.'))
            return redirect('complaints:detail', pk=pk)
    else:
        form = ComplaintForm(instance=complaint)
        
    return render(request, 'complaints/create.html', {
        'form': form, 
        'editing': True,
        'complaint': complaint
    })


@login_required
def vote_view(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    complaint = get_object_or_404(Complaint, pk=pk)
    
    # Do not allow voting on withdrawn complaints
    if complaint.status == Complaint.STATUS_WITHDRAWN:
        return JsonResponse({'error': 'Cannot vote on a withdrawn complaint'}, status=400)

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


@login_required
def export_single_complaint_pdf(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    
    context = {'complaint': complaint}
    html_string = render_to_string('complaints/single_complaint_pdf.html', context, request=request)
    
    response = HttpResponse(content_type='application/pdf')
    safe_title = "".join(c for c in complaint.title if c.isalnum() or c in (' ', '_', '-')).rstrip()
    response['Content-Disposition'] = f'inline; filename="Incident_Report_{complaint.pk}_{safe_title[:20]}.pdf"'
    
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response


@login_required
def withdraw_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk, author=request.user)

    if complaint.status != Complaint.STATUS_PENDING:
        messages.error(request, _('Only pending complaints can be withdrawn.'))
        return redirect('complaints:detail', pk=pk)

    if request.method == 'POST':
        complaint.status = Complaint.STATUS_WITHDRAWN
        complaint.save(update_fields=['status'])

        StatusLog.objects.create(
            complaint=complaint,
            changed_by=request.user,
            old_status=Complaint.STATUS_PENDING,
            new_status=Complaint.STATUS_WITHDRAWN,
            note=_('Withdrawn by user.')
        )

        messages.success(request, _('Complaint withdrawn successfully.'))
        return redirect('complaints:my_complaints')

    return render(request, 'complaints/withdraw_confirm.html', {'complaint': complaint})
=======
from django.shortcuts import render, redirect
from .models import Complaint

def submit_complaint(request):
    if request.method == "POST":
        title = request.POST['title']
        description = request.POST['description']
        category = request.POST['category']

        complaint = Complaint.objects.create(
            user=request.user,
            title=title,
            description=description,
            category=category
        )

        return redirect('complaint_success')

    return render(request, 'submit_complaint.html')
>>>>>>> 8c142e1c3888d30903d3e352271c439708bfc593

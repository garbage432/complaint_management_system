from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Comment
from .forms import CommentForm
from complaints.models import Complaint


@login_required
@require_POST
def add_comment(request, complaint_pk):
    complaint = get_object_or_404(Complaint, pk=complaint_pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.complaint = complaint
        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                comment.parent = Comment.objects.get(pk=parent_id, complaint=complaint)
            except Comment.DoesNotExist:
                pass
        comment.save()
        messages.success(request, 'Comment posted.')
    else:
        messages.error(request, 'Could not post comment.')
    return redirect('complaints:detail', pk=complaint_pk)


@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    complaint_pk = comment.complaint.pk
    comment.delete()
    messages.success(request, 'Comment deleted.')
    return redirect('complaints:detail', pk=complaint_pk)

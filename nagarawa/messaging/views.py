from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from .models import Conversation, Message
from .forms import MessageForm, StartConversationForm


def _get_staff_user():
    """Return the first available staff user to assign new conversations to."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    staff = User.objects.filter(is_staff=True, is_active=True).first()
    return staff


@login_required
def inbox(request):
    """Show all conversations for the current user."""
    user = request.user

    if user.is_staff:
        # Staff see ALL conversations
        conversations = Conversation.objects.select_related(
            'participant_citizen', 'participant_staff', 'complaint'
        ).prefetch_related('messages').order_by('-updated_at')

        # Filter options for staff
        filter_closed = request.GET.get('closed', '')
        if filter_closed == '1':
            conversations = conversations.filter(is_closed=True)
        elif filter_closed == '0' or not filter_closed:
            conversations = conversations.filter(is_closed=False)

        search = request.GET.get('q', '').strip()
        if search:
            conversations = conversations.filter(
                Q(participant_citizen__username__icontains=search) |
                Q(subject__icontains=search) |
                Q(complaint__title__icontains=search)
            )
    else:
        # Citizens see only their own conversations
        conversations = Conversation.objects.filter(
            participant_citizen=user
        ).select_related('participant_staff', 'complaint').prefetch_related('messages').order_by('-updated_at')

    # Attach unread counts
    conv_list = []
    for conv in conversations:
        conv.unread = conv.unread_count_for(user)
        conv.last_msg = conv.last_message()
        conv_list.append(conv)

    total_unread = sum(c.unread for c in conv_list)

    return render(request, 'messaging/inbox.html', {
        'conversations': conv_list,
        'total_unread': total_unread,
        'is_staff': user.is_staff,
        'filter_closed': request.GET.get('closed', '0'),
        'search': request.GET.get('q', ''),
    })


@login_required
def conversation_detail(request, pk):
    """View and reply to a conversation thread."""
    user = request.user
    conv = get_object_or_404(Conversation, pk=pk)

    # Access control
    if not user.is_staff and conv.participant_citizen != user:
        django_messages.error(request, 'You do not have access to this conversation.')
        return redirect('messaging:inbox')

    # Mark all unread messages as read
    conv.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    msg_form = MessageForm()
    all_messages = conv.messages.select_related('sender').order_by('created_at')

    return render(request, 'messaging/conversation.html', {
        'conv': conv,
        'msg_form': msg_form,
        'all_messages': all_messages,
        'other_user': conv.get_other_participant(user),
    })


@login_required
@require_POST
def send_message(request, pk):
    """Send a message in a conversation (AJAX or form POST)."""
    user = request.user
    conv = get_object_or_404(Conversation, pk=pk)

    if not user.is_staff and conv.participant_citizen != user:
        return JsonResponse({'error': 'Access denied'}, status=403)

    if conv.is_closed:
        return JsonResponse({'error': 'This conversation is closed.'}, status=400)

    form = MessageForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid message.'}, status=400)

    msg = Message.objects.create(
        conversation=conv,
        sender=user,
        body=form.cleaned_data['body']
    )

    # Touch conversation updated_at
    conv.save(update_fields=['updated_at'])

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return JsonResponse({
            'id': msg.pk,
            'body': msg.body,
            'sender_name': user.display_name,
            'sender_initial': user.username[0].upper(),
            'is_self': True,
            'created_at': msg.created_at.strftime('%H:%M'),
            'created_date': msg.created_at.strftime('%b %d, %Y'),
        })

    return redirect('messaging:conversation', pk=pk)


@login_required
def poll_messages(request, pk):
    """Return messages newer than a given timestamp for live polling."""
    user = request.user
    conv = get_object_or_404(Conversation, pk=pk)

    if not user.is_staff and conv.participant_citizen != user:
        return JsonResponse({'error': 'Access denied'}, status=403)

    since_id = request.GET.get('since_id', 0)
    try:
        since_id = int(since_id)
    except (ValueError, TypeError):
        since_id = 0

    new_messages = conv.messages.filter(pk__gt=since_id).select_related('sender').order_by('created_at')

    # Mark newly fetched messages as read if not from self
    new_messages.exclude(sender=user).update(is_read=True)

    return JsonResponse({
        'messages': [
            {
                'id': m.pk,
                'body': m.body,
                'sender_name': m.sender.display_name,
                'sender_initial': m.sender.username[0].upper(),
                'is_self': m.sender == user,
                'created_at': m.created_at.strftime('%H:%M'),
                'created_date': m.created_at.strftime('%b %d, %Y'),
            }
            for m in new_messages
        ]
    })


@login_required
def start_conversation(request, complaint_pk=None):
    """Citizen starts a new conversation, optionally linked to a complaint."""
    from complaints.models import Complaint

    complaint = None
    if complaint_pk:
        complaint = get_object_or_404(Complaint, pk=complaint_pk)

    # Citizens only — staff use the inbox to initiate
    if request.user.is_staff:
        django_messages.info(request, 'Staff can reply from the inbox.')
        return redirect('messaging:inbox')

    # Check if a conversation for this complaint already exists
    if complaint:
        existing = Conversation.objects.filter(
            participant_citizen=request.user,
            complaint=complaint,
            is_closed=False
        ).first()
        if existing:
            return redirect('messaging:conversation', pk=existing.pk)

    staff_user = _get_staff_user()
    if not staff_user:
        django_messages.error(request, 'No staff members are available right now. Please try again later.')
        return redirect('complaints:feed')

    if request.method == 'POST':
        form = StartConversationForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data.get('subject', '')
            if not subject and complaint:
                subject = f'Re: {complaint.title}'

            conv = Conversation.objects.create(
                participant_citizen=request.user,
                participant_staff=staff_user,
                complaint=complaint,
                subject=subject or 'General Enquiry',
            )
            Message.objects.create(
                conversation=conv,
                sender=request.user,
                body=form.cleaned_data['body']
            )
            django_messages.success(request, 'Message sent! You will receive a reply soon.')
            return redirect('messaging:conversation', pk=conv.pk)
    else:
        initial_subject = f'Re: {complaint.title}' if complaint else ''
        form = StartConversationForm(initial={'subject': initial_subject})

    return render(request, 'messaging/start_conversation.html', {
        'form': form,
        'complaint': complaint,
        'staff_user': staff_user,
    })


@login_required
@require_POST
def close_conversation(request, pk):
    """Staff can close a conversation."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Only staff can close conversations.'}, status=403)
    conv = get_object_or_404(Conversation, pk=pk)
    conv.is_closed = True
    conv.save(update_fields=['is_closed', 'updated_at'])
    django_messages.success(request, 'Conversation closed.')
    return redirect('messaging:inbox')


@login_required
@require_POST
def reopen_conversation(request, pk):
    """Staff can reopen a closed conversation."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Only staff can reopen conversations.'}, status=403)
    conv = get_object_or_404(Conversation, pk=pk)
    conv.is_closed = False
    conv.save(update_fields=['is_closed', 'updated_at'])
    django_messages.success(request, 'Conversation reopened.')
    return redirect('messaging:conversation', pk=pk)


@login_required
def unread_count_api(request):
    """Fast endpoint for navbar badge polling."""
    user = request.user
    if user.is_staff:
        count = Message.objects.filter(
            conversation__participant_staff=user,
            is_read=False
        ).exclude(sender=user).count()
    else:
        count = Message.objects.filter(
            conversation__participant_citizen=user,
            is_read=False
        ).exclude(sender=user).count()
    return JsonResponse({'unread': count})

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db.models import Q
from .models import Conversation, Message
from .forms import MessageForm, StartConversationForm

from django.conf import settings
from django.core.mail import send_mail

from complaints.models import Notification
from departments.models import UserProfile


def _notify(recipient, title, body='', link=''):
    """Create a notification and email it, matching accounts/views.py's _send_notification pattern."""
    if recipient is None:
        return
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


def _is_dept_admin(user):
    """Matches the helper already defined in accounts/views.py."""
    try:
        return user.userprofile.is_department_admin
    except Exception:
        return False


def _get_department_admin(complaint=None):
    """
    Resolve who should handle a conversation:
    - If the complaint has a department, route to that department's admin
      (UserProfile.is_department_admin=True for that department).
    - If the department has no admin assigned, return None — the caller
      should show an error rather than silently routing to superadmin.
    - Only general enquiries (no complaint at all) fall back to the superuser.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if complaint:
        if complaint.department:
            profile = UserProfile.objects.filter(
                department=complaint.department,
                is_department_admin=True,
                user__is_active=True,
            ).select_related('user').first()
            return profile.user if profile else None
        return None

    # No complaint at all (general enquiry) — superuser handles these.
    return User.objects.filter(is_superuser=True, is_active=True).first()


@login_required
def inbox(request):
    """Show all conversations for the current user."""
    user = request.user

    if (user.is_superuser or _is_dept_admin(user)):
        # Staff / department admins see conversations assigned to them
        conversations = Conversation.objects.filter(
            participant_staff=user
        ).select_related(
            'participant_citizen', 'participant_staff', 'complaint'
        ).prefetch_related('messages').order_by('-updated_at')

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

    conv_list = []
    for conv in conversations:
        conv.unread = conv.unread_count_for(user)
        conv.last_msg = conv.last_message()
        conv_list.append(conv)

    total_unread = sum(c.unread for c in conv_list)

    return render(request, 'messaging/inbox.html', {
        'conversations': conv_list,
        'total_unread': total_unread,
        'is_staff': (user.is_superuser or _is_dept_admin(user)),
        'filter_closed': request.GET.get('closed', '0'),
        'search': request.GET.get('q', ''),
    })


@login_required
def conversation_detail(request, pk):
    """View and reply to a conversation thread."""
    user = request.user
    conv = get_object_or_404(Conversation, pk=pk)

    # Access control — either the citizen who started it, or the assigned
    # department admin/staff member it's routed to
    if conv.participant_citizen != user and conv.participant_staff != user and not (user.is_superuser or _is_dept_admin(user)):
        django_messages.error(request, _('You do not have access to this conversation.'))
        return redirect('messaging:inbox')

    conv.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    msg_form = MessageForm()
    all_messages = conv.messages.select_related('sender').order_by('created_at')

    return render(request, 'messaging/conversation.html', {
        'conv': conv,
        'msg_form': msg_form,
        'all_messages': all_messages,
        'other_user': conv.get_other_participant(user),
        'can_manage': user.is_superuser or _is_dept_admin(user),
    })


@login_required
@require_POST
def send_message(request, pk):
    """Send a message in a conversation (AJAX or form POST). Notifies the other participant."""
    user = request.user
    conv = get_object_or_404(Conversation, pk=pk)

    if conv.participant_citizen != user and conv.participant_staff != user and not (user.is_superuser or _is_dept_admin(user)):
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

    conv.save(update_fields=['updated_at'])

    # Notify the other participant (works both directions: citizen -> admin, admin -> citizen)
    other = conv.get_other_participant(user)
    _notify(
        other,
        title=_('New message from %(sender)s') % {'sender': user.display_name},
        body=conv.subject,
        link=reverse('messaging:conversation', kwargs={'pk': conv.pk}),
    )

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

    if conv.participant_citizen != user and conv.participant_staff != user and not (user.is_superuser or _is_dept_admin(user)):
        return JsonResponse({'error': 'Access denied'}, status=403)

    since_id = request.GET.get('since_id', 0)
    try:
        since_id = int(since_id)
    except (ValueError, TypeError):
        since_id = 0

    new_messages = conv.messages.filter(pk__gt=since_id).select_related('sender').order_by('created_at')
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
    """
    Citizen starts a new conversation, routed to the department admin
    responsible for the complaint's department. If there's no complaint
    (general enquiry), the citizen picks a department first, and the
    message routes to that department's admin instead of the superadmin.
    """
    from complaints.models import Complaint
    from departments.models import Department

    complaint = None
    if complaint_pk:
        complaint = get_object_or_404(Complaint, pk=complaint_pk)

    if (request.user.is_superuser or _is_dept_admin(request.user)):
        django_messages.info(request, _('Staff can reply from the inbox.'))
        return redirect('messaging:inbox')

    if complaint:
        existing = Conversation.objects.filter(
            participant_citizen=request.user,
            complaint=complaint,
            is_closed=False
        ).first()
        if existing:
            return redirect('messaging:conversation', pk=existing.pk)

    departments = Department.objects.filter(is_active=True).order_by('name') if not complaint else None

    if request.method == 'POST':
        form = StartConversationForm(request.POST)

        # Resolve staff_user AFTER validating input, using the picked
        # department for general enquiries instead of falling back blindly.
        staff_user = None
        selected_department = None
        if complaint:
            staff_user = _get_department_admin(complaint)
        else:
            dept_id = request.POST.get('department')
            if not dept_id:
                django_messages.error(request, _('Please select a department.'))
                return render(request, 'messaging/start_conversation.html', {
                    'form': form, 'complaint': complaint, 'departments': departments,
                })
            selected_department = get_object_or_404(Department, pk=dept_id)
            profile = UserProfile.objects.filter(
                department=selected_department, is_department_admin=True, user__is_active=True
            ).select_related('user').first()
            staff_user = profile.user if profile else None

        if not staff_user:
            dept_name = complaint.department.display_name if complaint and complaint.department else (
                selected_department.display_name if selected_department else None
            )
            if dept_name:
                django_messages.error(
                    request,
                    _('The %(dept)s department does not have an admin assigned yet. Please try again later.') % {'dept': dept_name}
                )
            else:
                django_messages.error(request, _('No staff members are available right now. Please try again later.'))
            return render(request, 'messaging/start_conversation.html', {
                'form': form, 'complaint': complaint, 'departments': departments,
            })

        if form.is_valid():
            subject = form.cleaned_data.get('subject', '')
            if not subject and complaint:
                subject = f'Re: {complaint.title}'
            elif not subject and selected_department:
                subject = f'{selected_department.display_name} — General Enquiry'

            conv = Conversation.objects.create(
                participant_citizen=request.user,
                participant_staff=staff_user,
                complaint=complaint,
                subject=subject or _('General Enquiry'),
            )
            Message.objects.create(
                conversation=conv,
                sender=request.user,
                body=form.cleaned_data['body']
            )

            _notify(
                staff_user,
                title=_('New conversation from %(sender)s') % {'sender': request.user.display_name},
                body=conv.subject,
                link=reverse('messaging:conversation', kwargs={'pk': conv.pk}),
            )

            django_messages.success(request, _('Message sent! You will receive a reply soon.'))
            return redirect('messaging:conversation', pk=conv.pk)
    else:
        initial_subject = f'Re: {complaint.title}' if complaint else ''
        form = StartConversationForm(initial={'subject': initial_subject})

    return render(request, 'messaging/start_conversation.html', {
        'form': form,
        'complaint': complaint,
        'departments': departments,
    })


@login_required
@require_POST
def close_conversation(request, pk):
    """Department admin / staff can close a conversation."""
    conv = get_object_or_404(Conversation, pk=pk)
    if not (request.user.is_superuser or _is_dept_admin(request.user)) and conv.participant_staff != request.user:
        return JsonResponse({'error': 'Only the assigned admin or staff can close conversations.'}, status=403)
    conv.is_closed = True
    conv.save(update_fields=['is_closed', 'updated_at'])
    django_messages.success(request, _('Conversation closed.'))

    _notify(
        conv.participant_citizen,
        title=_('Conversation closed'),
        body=conv.subject,
        link=reverse('messaging:conversation', kwargs={'pk': conv.pk}),
    )
    return redirect('messaging:inbox')


@login_required
@require_POST
def reopen_conversation(request, pk):
    """Department admin / staff can reopen a closed conversation."""
    conv = get_object_or_404(Conversation, pk=pk)
    if not (request.user.is_superuser or _is_dept_admin(request.user)) and conv.participant_staff != request.user:
        return JsonResponse({'error': 'Only the assigned admin or staff can reopen conversations.'}, status=403)
    conv.is_closed = False
    conv.save(update_fields=['is_closed', 'updated_at'])
    django_messages.success(request, _('Conversation reopened.'))

    _notify(
        conv.participant_citizen,
        title=_('Conversation reopened'),
        body=conv.subject,
        link=reverse('messaging:conversation', kwargs={'pk': conv.pk}),
    )
    return redirect('messaging:conversation', pk=pk)


@login_required
def unread_count_api(request):
    """Fast endpoint for navbar badge polling."""
    user = request.user
    if (user.is_superuser or _is_dept_admin(user)):
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
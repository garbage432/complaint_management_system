
import os
from django.shortcuts import render, redirect
from complaints.models import Complaint
from departments.models import Department
from django.contrib.auth import get_user_model

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()


def _build_feed_snapshot(limit=8):
    complaints = Complaint.objects.select_related('author', 'department').order_by('-created_at')[:limit]
    if not complaints:
        return "No complaints available yet."

    lines = []
    for index, complaint in enumerate(complaints, start=1):
        dept_name = complaint.department.name if complaint.department else 'Unassigned'
        status_label = complaint.get_status_display() if hasattr(complaint, 'get_status_display') else complaint.status
        author_name = getattr(complaint.author, 'username', 'unknown')
        lines.append(
            f"{index}. {complaint.title} | status={status_label} | department={dept_name} | created_at={complaint.created_at.strftime('%Y-%m-%d %H:%M')} | author={author_name}"
        )
    return "\n".join(lines)


def _build_basic_reply(user_message, feed_snapshot):
    message = (user_message or "").strip().lower()
    if any(keyword in message for keyword in ["latest", "recent", "feed", "complaint"]):
        return (
            "Here are the latest complaints from Samparka:\n"
            f"{feed_snapshot}"
        )

    if any(keyword in message for keyword in ["department", "dept", "which department", "departments"]):
        return (
            "Available departments include: Agriculture, Police & Security, Roads & Transport, "
            "Urban Planning, Water Supply, Waste Management, Social Welfare, and Revenue and Tax."
        )

    if any(keyword in message for keyword in ["status", "pending", "verified", "in progress", "solved", "rejected"]):
        return (
            "Complaint statuses in Samparka are: Pending, Verified, In Progress, Solved, and Rejected."
        )

    if any(keyword in message for keyword in ["agriculture", "farm", "fertilizer", "pesticide", "irrigation", "crop", "livestock"]):
        return "This sounds like an Agriculture-related issue. Please route it to the Agriculture department."

    if any(keyword in message for keyword in ["hello", "hi", "hey", "help", "who are you", "what can you do"]):
        return (
            "Hello! I can help you check recent complaints, explain departments, share status updates, "
            "and guide you through Samparka."
        )

    return (
        "I can help with recent complaints, department names, statuses, and basic Samparka guidance. "
        "Try asking about recent complaints or a department."
    )


def _normalize_chat_reply(reply, user_message, feed_snapshot):
    reply = (reply or "").strip()
    if not reply:
        return _build_basic_reply(user_message, feed_snapshot)
    if "[Fallback]" in reply or "[Error]" in reply or "HTTP Error" in reply:
        return _build_basic_reply(user_message, feed_snapshot)
    return reply


def home_view(request):
    recent = Complaint.objects.select_related('author', 'department').order_by('-created_at')[:6]

    stats = {
        'total_complaints': Complaint.objects.count(),
        'solved': Complaint.objects.filter(status='solved').count(),
        'in_progress': Complaint.objects.filter(status='in_progress').count(),
        'total_users': User.objects.count(),
    }

    departments = Department.objects.filter(is_active=True)

    return render(request, 'core/home.html', {
        'recent_complaints': recent,
        'stats': stats,
        'departments': departments,
    })


def feed(request):
    return render(request, "complaints/feed.html")


@csrf_exempt
def chatbot(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "")
        feed_snapshot = _build_feed_snapshot()

        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            return JsonResponse({"reply": _build_basic_reply(user_message, feed_snapshot)})

        from urllib import request as urllib_request
        from urllib.error import HTTPError, URLError

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": f"""You are a helpful assistant for Samparka, a civic complaint management platform in Nepal.

DEPARTMENTS AVAILABLE:
- Police & Security, Public Safety, Revenue and Tax
- Roads & Transport, Social Welfare, Transport
- Urban Planning, Waste Management, Water Supply, Women and Children
- Agriculture

COMPLAINT STATUS: Pending → Verified → In Progress → Solved / Rejected
PRIORITY LEVELS: Low, Medium, High, Urgent

CURRENT FEED SNAPSHOT (latest complaints from the app):
{feed_snapshot}

WHAT USERS CAN DO:
- Register, login, post complaints, upload images
- Post anonymously, upvote/downvote, comment
- Track status in dashboard, rate resolved complaints

IMPORTANT:
- If the user mentions farming, irrigation, seeds, fertilizers, pesticides, crop disease, livestock, subsidies, or agricultural services, treat it as an Agriculture-related issue.
- Use the CURRENT FEED SNAPSHOT when the user asks about recent complaints, trends, or status changes.
- When you list complaints, number them exactly as 1, 2, 3, ... in the same order as the CURRENT FEED SNAPSHOT.
- Use the department names from the CURRENT FEED SNAPSHOT exactly as written; do not invent, merge, or rename departments.
- Keep answers short and helpful. Respond in Nepali if user writes in Nepali."""},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 500
        }

        req = urllib_request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:
            with urllib_request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError:
            return JsonResponse({"reply": _build_basic_reply(user_message, feed_snapshot)})
        except URLError:
            return JsonResponse({"reply": _build_basic_reply(user_message, feed_snapshot)})
        except Exception:
            return JsonResponse({"reply": _build_basic_reply(user_message, feed_snapshot)})

        if "choices" in data and data["choices"]:
            reply = data["choices"][0]["message"]["content"]
        elif "error" in data:
            reply = data['error'].get('message', 'Unknown error from Groq API.')
        else:
            reply = ""
        return JsonResponse({"reply": _normalize_chat_reply(reply, user_message, feed_snapshot)})

    return JsonResponse({"error": "Invalid request"}, status=400)
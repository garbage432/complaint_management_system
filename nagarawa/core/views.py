
import os
from django.shortcuts import render, redirect
from complaints.models import Complaint
from departments.models import Department
from django.contrib.auth import get_user_model

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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


@csrf_exempt
def chatbot(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "")

        import requests as http_requests
        
        response = http_requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY', '')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": """You are a helpful assistant for Samparka, a civic complaint management platform in Nepal.

DEPARTMENTS AVAILABLE:
- Police & Security, Public Safety, Revenue and Tax
- Roads & Transport, Social Welfare, Transport
- Urban Planning, Waste Management, Water Supply, Women and Children

COMPLAINT STATUS: Pending → Verified → In Progress → Solved / Rejected
PRIORITY LEVELS: Low, Medium, High, Urgent

WHAT USERS CAN DO:
- Register, login, post complaints, upload images
- Post anonymously, upvote/downvote, comment
- Track status in dashboard, rate resolved complaints

Keep answers short and helpful. Respond in Nepali if user writes in Nepali."""},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 500
            }
        )
        
        data = response.json()
        if "choices" in data and data["choices"]:
            reply = data["choices"][0]["message"]["content"]
        elif "error" in data:
            reply = f"[Error] {data['error'].get('message', 'Unknown error from Groq API.')}"
        else:
            reply = "[Error] Unexpected response from Groq API."
        return JsonResponse({"reply": reply})

    return JsonResponse({"error": "Invalid request"}, status=400)
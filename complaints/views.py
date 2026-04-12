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

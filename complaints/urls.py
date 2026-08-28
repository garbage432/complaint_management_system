from django.urls import path
from . import views

<<<<<<< HEAD
app_name = 'complaints'

urlpatterns = [
    path('', views.feed_view, name='feed'),
    path('create/', views.complaint_create, name='create'),
    path('<int:pk>/', views.complaint_detail, name='detail'),
    path('<int:pk>/edit/', views.complaint_edit, name='edit'),
    path('<int:pk>/vote/', views.vote_view, name='vote'),
    path('my/', views.my_complaints, name='my_complaints'),
    path('complaint/<int:pk>/export/pdf/', views.export_single_complaint_pdf, name='export_single_complaint_pdf'),
    path('<int:pk>/withdraw/', views.withdraw_complaint, name='withdraw'),
]
=======
urlpatterns = [
    path('submit/', views.submit_complaint, name='submit_complaint'),
]
>>>>>>> 8c142e1c3888d30903d3e352271c439708bfc593

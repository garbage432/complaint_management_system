from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('', views.feed_view, name='feed'),
    path('create/', views.complaint_create, name='create'),
    path('<int:pk>/', views.complaint_detail, name='detail'),
    path('<int:pk>/edit/', views.complaint_edit, name='edit'),
    path('<int:pk>/vote/', views.vote_view, name='vote'),
    path('my/', views.my_complaints, name='my_complaints'),
]

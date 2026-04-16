from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    path('complaint/<int:complaint_pk>/add/', views.add_comment, name='add'),
    path('<int:pk>/delete/', views.delete_comment, name='delete'),
]

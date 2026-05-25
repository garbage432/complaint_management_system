from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('start/', views.start_conversation, name='start'),
    path('start/<int:complaint_pk>/', views.start_conversation, name='start_for_complaint'),
    path('<int:pk>/', views.conversation_detail, name='conversation'),
    path('<int:pk>/send/', views.send_message, name='send'),
    path('<int:pk>/poll/', views.poll_messages, name='poll'),
    path('<int:pk>/close/', views.close_conversation, name='close'),
    path('<int:pk>/reopen/', views.reopen_conversation, name='reopen'),
    path('api/unread/', views.unread_count_api, name='unread_count'),
]

from django.urls import path
from . import views

app_name = "core"

urlpatterns = [

    path("", views.home_view, name="home"),
    path("feed/", views.feed, name="feed"),
path("chatbot/", views.chatbot, name="chatbot"),
]
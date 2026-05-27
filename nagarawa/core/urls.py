from django.urls import path
from . import views

app_name = "core"

urlpatterns = [

    path(
        "",
        views.feed,
        name="feed"
    ),
path("chatbot/", views.chatbot, name="chatbot"),
]
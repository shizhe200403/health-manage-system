from django.urls import path

from . import views

urlpatterns = [
    path("conversations/", views.conversations),
    path("conversations/<int:pk>/", views.conversation_detail),
    path("conversations/<int:pk>/chat/", views.chat),
]

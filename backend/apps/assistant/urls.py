from django.urls import path

from . import views

urlpatterns = [
    path("conversations/", views.conversations),
    path("conversations/<int:pk>/", views.conversation_detail),
    path("conversations/<int:pk>/chat/", views.chat),
    path("food-image/analyze/", views.analyze_food_photo),
]

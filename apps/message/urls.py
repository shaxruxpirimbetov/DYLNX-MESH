from django.urls import path
from . import views

urlpatterns = [
    path("", views.MessageListCreateAPIView.as_view()),
    path("<int:pk>/", views.MessageDetailAPIView.as_view()),
]
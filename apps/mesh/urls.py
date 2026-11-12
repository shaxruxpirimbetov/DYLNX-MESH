from django.urls import path
from . import views

urlpatterns = [
    path("", views.MeshListCreateAPIView.as_view()),
    path("<int:pk>/", views.MeshDetailAPIView.as_view()),
    path("activate/<str:uuid>/", views.ActivateMeshAPIView.as_view()),
]
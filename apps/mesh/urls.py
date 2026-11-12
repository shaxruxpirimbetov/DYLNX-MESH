from django.urls import path
from . import views

urlpatterns = [
    path("", views.MeshListCreateAPIView.as_view()),
    path("<int:pk>/", views.MeshDetailAPIView.as_view()),
    path("open/<str:uuid>/", views.OpenMeshAPIView.as_view()),
]
from django.urls import path
from . import views

urlpatterns = [
    path("", views.MeshListCreateAPIView.as_view()),
    path("stats/", views.MeshStatsAPIView.as_view()),
    path("<int:pk>/", views.MeshDetailAPIView.as_view()),
    path("<int:pk>/regenerate-qr/", views.MeshRegenerateQRAPIView.as_view()),
    path("activate/<str:uuid>/", views.ActivateMeshAPIView.as_view()),
    path("uuid/<uuid:uuid>/", views.MeshByUUIDAPIView.as_view()),
]
from django.views import View
from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.response import Response
from apps.user.permissions import IsLisa
from decouple import config
from utils import QR
from .models import Mesh
from .serializers import MeshSerializer, ActivateMeshSerializer

BACKEND_HERE = config('BACKEND_HERE')

class MeshListCreateAPIView(generics.ListCreateAPIView):
    queryset = Mesh.objects.all()
    serializer_class = MeshSerializer
    permission_classes = [permissions.IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        qrcode = QR.make(serializer.instance.uuid)
        serializer.instance.qrcode = qrcode
        serializer.instance.url = f"{BACKEND_HERE}/mesh/{serializer.instance.uuid}"
        serializer.instance.save()
        return Response(serializer.data, status=201)

class MeshDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Mesh.objects.all()
    serializer_class = MeshSerializer
    permission_classes = [permissions.IsAdminUser]

class ActivateMeshAPIView(generics.UpdateAPIView):
    queryset = Mesh.objects.all()
    serializer_class = ActivateMeshSerializer
    permission_classes = [IsLisa]
    lookup_field = 'uuid'

class OpenMeshAPIView(View):
    permission_classes = [permissions.AllowAny]
    def get(self, request, uuid, *args, **kwargs):
        try:
            mesh = Mesh.objects.filter(uuid=uuid).first()
            if not mesh:
                return render(request, "invalid_uuid.html")

            if not mesh.is_active:
                return render(request, "unactive_qr.html")
            return render(request, "open_mesh.html")
        except Exception as err:
            return render(request, "invalid_uuid.html")
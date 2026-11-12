from django.views import View
from django.shortcuts import render
from rest_framework import generics, permissions, status
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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data['password'] != instance.password:
            return Response({"detail": "Passwords do not match."}, status=400)

        serializer.save()
        return Response(serializer.data, status=200)

class OpenMeshAPIView(View):
    permission_classes = [permissions.AllowAny]
    def get(self, request, uuid, *args, **kwargs):
        try:
            mesh = Mesh.objects.filter(uuid=uuid).first()
            if not mesh:
                return render(request, "invalid_uuid.html")

            if not mesh.is_active:
                return render(request, "unactive_qr.html")
            return render(request, "open_mesh.html", {"telegram": mesh.telegram_id, "phone": mesh.phone})
        except Exception as err:
            return render(request, "invalid_uuid.html")
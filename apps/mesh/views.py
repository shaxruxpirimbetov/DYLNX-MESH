from django.views import View
from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from decouple import config
from utils import QR
from .models import Mesh
from .serializers import MeshSerializer, ChangeAllPasswordSerializer

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

class OpenMeshAPIView(View):
    permission_classes = [permissions.AllowAny]
    def get(self, request, uuid, *args, **kwargs):
        try:
            mesh = Mesh.objects.filter(uuid=uuid).first()
            if not mesh:
                # return Response({"detail": f"mesh with this {uuid} uuid not found"}, status=404)
                return render(request, "invalid_uuid.html")

            if not mesh.phone:
                return render(request, "unactive_qr.html")
            return render(request, "invalid_uuid.html")
        except Exception as err:
            return render(request, "invalid_uuid.html")
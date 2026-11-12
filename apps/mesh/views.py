from django.db.models import CharField, Count, Q
from django.db.models.functions import Cast
from django.views import View
from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from apps.user.permissions import IsLisa
from decouple import config
from utils import QR
from datetime import timedelta
from rest_framework.views import APIView
from .models import Mesh
from .serializers import MeshSerializer, ActivateMeshSerializer
import logging
logger = logging.getLogger(__name__)

BACKEND_HERE = config('BACKEND_HERE')

class MeshListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MeshSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = Mesh.objects.select_related("user").annotate(messages_count=Count("message_mesh"))
        p = self.request.query_params
        today = timezone.localdate()
        if p.get("telegram_id"):
            qs = qs.filter(telegram_id=str(p["telegram_id"]))
        if p.get("until_lte"):
            qs = qs.filter(until__lte=p["until_lte"])
        status_ = p.get("status")
        if status_ == "active":
            qs = qs.filter(is_active=True, until__gte=today)
        elif status_ == "inactive":
            qs = qs.filter(is_active=False)
        elif status_ == "expired":
            qs = qs.filter(until__lt=today)
        search = (p.get("search") or "").strip()
        if search:
            qs = qs.annotate(uuid_str=Cast("uuid", CharField())).filter(
                Q(uuid_str__icontains=search) | Q(phone__icontains=search) | Q(telegram_id__icontains=search))
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        instance = serializer.instance
        instance.url = f"{BACKEND_HERE.rstrip('/')}/mesh/{instance.uuid}/"
        try:
            instance.qrcode = QR.make(instance.uuid)
        except Exception as err:
            logger.exception("QR upload failed for %s: %s", instance.uuid, err)
        instance.save()
        return Response(self.get_serializer(instance).data, status=201)

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
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "password" not in data or "telegram_id" not in data:
            return Response({"detail": "password and telegram_id are required."}, status=400)
        if data["password"] != instance.password:
            return Response({"detail": "Passwords do not match."}, status=400)
        if instance.is_active and instance.telegram_id and instance.telegram_id != str(data["telegram_id"]):
            return Response({"detail": "Mesh is already activated by another user."}, status=409)

        serializer.save(is_active=True, telegram_id=str(data["telegram_id"]))
        return Response(serializer.data, status=200)

class OpenMeshAPIView(View):
    def get(self, request, uuid, *args, **kwargs):
        base_ctx = {
            "uuid": uuid,
            "bot_username": settings.TELEGRAM_BOT_USERNAME,
            "buy_url": settings.MESH_BUY_URL or f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start=buy",
        }
        try:
            mesh = Mesh.objects.filter(uuid=uuid).first()
        except Exception:
            mesh = None

        if not mesh:
            return render(request, "invalid_uuid.html", base_ctx, status=404)

        expired = bool(mesh.until and mesh.until < timezone.localdate())
        if not mesh.is_active or not mesh.telegram_id or expired:
            return render(request, "unactive_qr.html", {**base_ctx, "expired": expired})

        # telegram_id в шаблон НЕ передаём — иначе он виден в исходнике страницы
        return render(request, "open_mesh.html", {**base_ctx, "phone": mesh.phone or ""})

class MeshByUUIDAPIView(generics.RetrieveUpdateAPIView):
    queryset = Mesh.objects.all()
    serializer_class = MeshSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = "uuid"


class MeshStatsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from apps.message.models import Message
        today = timezone.localdate()
        soon = today + timedelta(days=7)
        qs = Mesh.objects.all()
        return Response({
            "total": qs.count(),
            "active": qs.filter(is_active=True, until__gte=today).count(),
            "inactive": qs.filter(is_active=False).count(),
            "expired": qs.filter(until__lt=today).count(),
            "expiring_soon": qs.filter(is_active=True, until__gte=today, until__lte=soon).count(),
            "owners": qs.exclude(telegram_id__isnull=True).exclude(telegram_id="")
            .values("telegram_id").distinct().count(),
            "messages": Message.objects.count(),
            "messages_today": Message.objects.filter(created_at__date=today).count(),
        })


class MeshRegenerateQRAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        mesh = generics.get_object_or_404(Mesh, pk=pk)
        mesh.url = f"{BACKEND_HERE.rstrip('/')}/mesh/{mesh.uuid}/"
        try:
            mesh.qrcode = QR.make(mesh.uuid)
        except Exception as err:
            return Response({"detail": f"QR upload failed: {err}"}, status=502)
        mesh.save(update_fields=["qrcode", "url", "updated_at"])
        return Response(MeshSerializer(mesh).data)
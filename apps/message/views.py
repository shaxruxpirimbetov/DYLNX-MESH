from rest_framework import generics, permissions
from .models import Message
from .serializers import MessageSerializer

class MessageListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = Message.objects.select_related("mesh")
        p = self.request.query_params
        if p.get("mesh"):
            qs = qs.filter(mesh_id=p["mesh"])
        if p.get("search"):
            qs = qs.filter(message__icontains=p["search"])
        if p.get("after_id"):
            qs = qs.filter(id__gt=p["after_id"]).order_by("id")   # для поллинга
        return qs

class MessageDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAdminUser]
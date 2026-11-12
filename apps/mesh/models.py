from django.contrib.auth import get_user_model
from django.db import models
import uuid
User = get_user_model()

class Mesh(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mesh_user")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    telegram_id = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    until = models.DateField()
    # password = models.CharField(max_length=100, null=True, blank=True)

    qrcode = models.URLField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Mesh {self.uuid}"

    class Meta:
        verbose_name = "Mesh"
        verbose_name_plural = "Meshes"
        ordering = ["-created_at"]
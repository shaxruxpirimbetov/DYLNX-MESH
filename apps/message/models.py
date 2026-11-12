from django.db import models
from apps.mesh.models import Mesh

class Message(models.Model):
    mesh = models.ForeignKey(Mesh, on_delete=models.CASCADE, related_name='message_mesh')
    telegram_id = models.IntegerField(default=0)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_author(self):
        return True if self.telegram_id == self.mesh.telegram_id else False

    def __str__(self):
        return f"Message for Mesh({self.mesh.uuid}): {self.message[10:]} {'...' if len(self.message) > 10 else ''}"

    class Meta:
        verbose_name_plural = "Messages"
        ordering = ["-created_at"]
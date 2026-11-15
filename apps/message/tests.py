from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.mesh.models import Mesh

from .models import Message

User = get_user_model()


class MessageAPITests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user("staff", password="pass12345", is_staff=True)
        self.user = User.objects.create_user("user", password="pass12345")
        self.mesh = Mesh.objects.create(
            user=self.staff,
            until=timezone.localdate() + timedelta(days=30),
            password="CODE123",
            telegram_id="111",
            is_active=True,
        )
        self.client = APIClient()

    def create_message(self, text="hello", telegram_id=222, mesh=None):
        return Message.objects.create(
            mesh=mesh or self.mesh, message=text, telegram_id=telegram_id
        )

    # --- access control: anonymous chats must stay private ---

    def test_anonymous_cannot_read_messages(self):
        self.create_message()
        self.assertEqual(self.client.get("/api/message/").status_code, 401)

    def test_anonymous_cannot_post_messages(self):
        response = self.client.post(
            "/api/message/", {"mesh": self.mesh.pk, "message": "hi"}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_regular_user_cannot_read_messages(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/message/").status_code, 403)

    def test_regular_user_cannot_open_single_message(self):
        message = self.create_message()
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(f"/api/message/{message.pk}/").status_code, 403)

    # --- staff (the bot and the admin panel) ---

    def test_staff_can_create_message(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            "/api/message/",
            {"mesh": self.mesh.pk, "message": "car is blocking the road", "telegram_id": 222},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.objects.get().telegram_id, 222)

    def test_telegram_id_is_stored_as_big_integer(self):
        big_id = 7_000_000_000  # does not fit into a 32-bit integer
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            "/api/message/",
            {"mesh": self.mesh.pk, "message": "hi", "telegram_id": big_id},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.objects.get().telegram_id, big_id)

    def test_response_exposes_owner_and_author_flag(self):
        self.create_message("from guest", telegram_id=222)
        self.create_message("from owner", telegram_id=111)
        self.client.force_authenticate(self.staff)

        results = {
            item["message"]: item for item in self.client.get("/api/message/").json()["results"]
        }
        self.assertFalse(results["from guest"]["is_author"])
        self.assertTrue(results["from owner"]["is_author"])
        self.assertEqual(results["from guest"]["owner_telegram_id"], "111")
        self.assertEqual(results["from guest"]["mesh_uuid"], str(self.mesh.uuid))

    def test_admin_panel_messages_use_telegram_id_zero(self):
        message = self.create_message("from admin panel", telegram_id=0)
        self.assertFalse(message.is_author)

    # --- filters ---

    def test_filter_by_mesh(self):
        other = Mesh.objects.create(
            user=self.staff,
            until=timezone.localdate() + timedelta(days=30),
            password="OTHER",
        )
        self.create_message("mine")
        self.create_message("not mine", mesh=other)
        self.client.force_authenticate(self.staff)

        response = self.client.get(f"/api/message/?mesh={self.mesh.pk}")
        self.assertEqual([m["message"] for m in response.json()["results"]], ["mine"])

    def test_search_in_text(self):
        self.create_message("blocking the driveway")
        self.create_message("found your wallet")
        self.client.force_authenticate(self.staff)

        response = self.client.get("/api/message/?search=wallet")
        self.assertEqual([m["message"] for m in response.json()["results"]], ["found your wallet"])

    def test_after_id_returns_only_newer_messages_in_ascending_order(self):
        first = self.create_message("one")
        second = self.create_message("two")
        third = self.create_message("three")
        self.client.force_authenticate(self.staff)

        response = self.client.get(f"/api/message/?after_id={first.pk}")
        ids = [m["id"] for m in response.json()["results"]]
        self.assertEqual(ids, [second.pk, third.pk])  # the bot poller relies on this order

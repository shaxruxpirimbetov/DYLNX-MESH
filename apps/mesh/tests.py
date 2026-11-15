from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Mesh

User = get_user_model()

QR_MAKE = "apps.mesh.views.QR.make"
FAKE_QR_URL = "https://cdn.example.com/qrcode/test.png"


def make_mesh(owner, **kwargs):
    """Create a sticker directly in the database."""
    data = {
        "user": owner,
        "until": timezone.localdate() + timedelta(days=30),
        "password": "CODE123",
    }
    data.update(kwargs)
    return Mesh.objects.create(**data)


class BaseAPITestCase(TestCase):
    def setUp(self):
        cache.clear()  # throttling counters live in the cache
        self.staff = User.objects.create_user("staff", password="pass12345", is_staff=True)
        self.user = User.objects.create_user("user", password="pass12345")
        self.client = APIClient()

    def as_staff(self):
        self.client.force_authenticate(self.staff)

    def as_user(self):
        self.client.force_authenticate(self.user)


class MeshAccessTests(BaseAPITestCase):
    def test_anonymous_cannot_list_stickers(self):
        self.assertEqual(self.client.get("/api/mesh/").status_code, 401)

    def test_regular_user_cannot_list_stickers(self):
        self.as_user()
        self.assertEqual(self.client.get("/api/mesh/").status_code, 403)

    def test_regular_user_cannot_see_stats(self):
        self.as_user()
        self.assertEqual(self.client.get("/api/mesh/stats/").status_code, 403)

    def test_staff_can_list_stickers(self):
        make_mesh(self.staff)
        self.as_staff()
        response = self.client.get("/api/mesh/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)


class MeshCreateTests(BaseAPITestCase):
    payload = {"until": "2030-01-01", "password": "CODE123"}

    @patch(QR_MAKE, return_value=FAKE_QR_URL)
    def test_create_sets_owner_url_and_qr(self, qr_make):
        self.as_staff()
        response = self.client.post("/api/mesh/", self.payload, format="json")
        self.assertEqual(response.status_code, 201)

        mesh = Mesh.objects.get()
        self.assertEqual(mesh.user, self.staff)
        self.assertFalse(mesh.is_active)
        self.assertEqual(mesh.qrcode, FAKE_QR_URL)
        self.assertTrue(mesh.url.endswith(f"/mesh/{mesh.uuid}/"))
        qr_make.assert_called_once_with(mesh.uuid)

    @patch(QR_MAKE, side_effect=RuntimeError("R2 is down"))
    def test_create_succeeds_when_qr_upload_fails(self, _):
        self.as_staff()
        response = self.client.post("/api/mesh/", self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(Mesh.objects.get().qrcode)

    @patch(QR_MAKE, return_value=FAKE_QR_URL)
    def test_regenerate_qr(self, _):
        mesh = make_mesh(self.staff)
        self.as_staff()
        response = self.client.post(f"/api/mesh/{mesh.pk}/regenerate-qr/")
        self.assertEqual(response.status_code, 200)
        mesh.refresh_from_db()
        self.assertEqual(mesh.qrcode, FAKE_QR_URL)

    @patch(QR_MAKE, side_effect=RuntimeError("R2 is down"))
    def test_regenerate_qr_reports_upload_failure(self, _):
        mesh = make_mesh(self.staff)
        self.as_staff()
        response = self.client.post(f"/api/mesh/{mesh.pk}/regenerate-qr/")
        self.assertEqual(response.status_code, 502)


class MeshFilterTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        today = timezone.localdate()
        self.active = make_mesh(self.staff, is_active=True, telegram_id="111", phone="+998901112233")
        self.inactive = make_mesh(self.staff, is_active=False)
        self.expired = make_mesh(
            self.staff, is_active=True, telegram_id="222", until=today - timedelta(days=1)
        )
        self.as_staff()

    def uuids(self, query):
        response = self.client.get(f"/api/mesh/?{query}")
        self.assertEqual(response.status_code, 200)
        return {item["uuid"] for item in response.json()["results"]}

    def test_filter_active(self):
        self.assertEqual(self.uuids("status=active"), {str(self.active.uuid)})

    def test_filter_inactive(self):
        self.assertEqual(self.uuids("status=inactive"), {str(self.inactive.uuid)})

    def test_filter_expired(self):
        self.assertEqual(self.uuids("status=expired"), {str(self.expired.uuid)})

    def test_filter_by_telegram_id(self):
        self.assertEqual(self.uuids("telegram_id=111"), {str(self.active.uuid)})

    def test_search_by_phone(self):
        self.assertEqual(self.uuids("search=901112233"), {str(self.active.uuid)})

    def test_search_by_uuid_fragment(self):
        fragment = str(self.inactive.uuid)[:8]
        self.assertIn(str(self.inactive.uuid), self.uuids(f"search={fragment}"))


class MeshPaginationTests(BaseAPITestCase):
    def test_pages_do_not_overlap_or_skip_items(self):
        created = [make_mesh(self.staff) for _ in range(5)]
        self.as_staff()

        seen = []
        for page in (1, 2, 3):
            response = self.client.get(f"/api/mesh/?page_size=2&page={page}")
            self.assertEqual(response.status_code, 200)
            seen += [item["id"] for item in response.json()["results"]]

        self.assertEqual(len(seen), 5)
        self.assertEqual(set(seen), {m.pk for m in created})
        self.assertEqual(seen, sorted(seen, reverse=True))  # newest first


class MeshStatsTests(BaseAPITestCase):
    def test_stats_counts(self):
        today = timezone.localdate()
        make_mesh(self.staff, is_active=True, telegram_id="111")
        make_mesh(self.staff, is_active=True, telegram_id="111", until=today + timedelta(days=3))
        make_mesh(self.staff, is_active=False)
        make_mesh(self.staff, is_active=True, telegram_id="222", until=today - timedelta(days=2))
        self.as_staff()

        data = self.client.get("/api/mesh/stats/").json()
        self.assertEqual(data["total"], 4)
        self.assertEqual(data["active"], 2)
        self.assertEqual(data["inactive"], 1)
        self.assertEqual(data["expired"], 1)
        self.assertEqual(data["expiring_soon"], 1)
        self.assertEqual(data["owners"], 2)  # distinct telegram ids: 111 and 222


class ActivationTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.mesh = make_mesh(self.staff)
        self.url = f"/api/mesh/activate/{self.mesh.uuid}/"
        self.as_staff()  # the bot acts through a staff account

    def activate(self, **payload):
        return self.client.patch(self.url, payload, format="json")

    def test_anonymous_cannot_activate(self):
        self.client.force_authenticate(None)
        response = self.activate(password="CODE123", telegram_id=1)
        self.assertEqual(response.status_code, 401)

    def test_activation_binds_telegram_account(self):
        response = self.activate(password="CODE123", telegram_id=111, phone="+998901112233")
        self.assertEqual(response.status_code, 200)
        self.mesh.refresh_from_db()
        self.assertTrue(self.mesh.is_active)
        self.assertEqual(self.mesh.telegram_id, "111")
        self.assertEqual(self.mesh.phone, "+998901112233")

    def test_activation_does_not_leak_secret_code(self):
        response = self.activate(password="CODE123", telegram_id=111)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.json())

    def test_activation_returns_expiry_date_for_the_bot(self):
        response = self.activate(password="CODE123", telegram_id=111)
        self.assertEqual(response.json()["until"], self.mesh.until.isoformat())

    def test_activation_cannot_change_expiry_date(self):
        response = self.activate(password="CODE123", telegram_id=111, until="2099-01-01")
        self.assertEqual(response.status_code, 200)
        self.mesh.refresh_from_db()
        self.assertNotEqual(self.mesh.until.isoformat(), "2099-01-01")

    def test_wrong_code_is_rejected(self):
        response = self.activate(password="WRONG", telegram_id=111)
        self.assertEqual(response.status_code, 400)
        self.mesh.refresh_from_db()
        self.assertFalse(self.mesh.is_active)

    def test_missing_fields_are_rejected(self):
        self.assertEqual(self.activate(password="CODE123").status_code, 400)
        self.assertEqual(self.activate(telegram_id=111).status_code, 400)

    def test_sticker_cannot_be_taken_over_by_another_account(self):
        self.activate(password="CODE123", telegram_id=111)
        response = self.activate(password="CODE123", telegram_id=222)
        self.assertEqual(response.status_code, 409)
        self.mesh.refresh_from_db()
        self.assertEqual(self.mesh.telegram_id, "111")

    def test_same_owner_can_activate_again(self):
        self.activate(password="CODE123", telegram_id=111)
        response = self.activate(password="CODE123", telegram_id=111)
        self.assertEqual(response.status_code, 200)

    def test_unknown_uuid_returns_404(self):
        response = self.client.patch(
            "/api/mesh/activate/00000000-0000-0000-0000-000000000000/",
            {"password": "CODE123", "telegram_id": 111},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


class PublicPageTests(BaseAPITestCase):
    def get_page(self, uuid):
        return self.client.get(f"/mesh/{uuid}/")

    def test_unknown_uuid_shows_not_found_page(self):
        response = self.get_page("00000000-0000-0000-0000-000000000000")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "invalid_uuid.html")

    def test_malformed_uuid_shows_not_found_page(self):
        response = self.get_page("not-a-uuid")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "invalid_uuid.html")

    def test_inactive_sticker_shows_activation_page(self):
        mesh = make_mesh(self.staff)
        response = self.get_page(mesh.uuid)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "unactive_qr.html")

    def test_expired_sticker_shows_activation_page(self):
        mesh = make_mesh(
            self.staff,
            is_active=True,
            telegram_id="111",
            until=timezone.localdate() - timedelta(days=1),
        )
        response = self.get_page(mesh.uuid)
        self.assertTemplateUsed(response, "unactive_qr.html")
        self.assertTrue(response.context["expired"])

    def test_active_sticker_opens_contact_page(self):
        mesh = make_mesh(self.staff, is_active=True, telegram_id="987654321")
        response = self.get_page(mesh.uuid)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "open_mesh.html")

    def test_owner_telegram_id_is_never_rendered(self):
        mesh = make_mesh(self.staff, is_active=True, telegram_id="987654321")
        response = self.get_page(mesh.uuid)
        self.assertNotContains(response, "987654321")

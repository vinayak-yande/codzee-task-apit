from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from tasks.models import Task

class ValidationTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="alice")
        self.client.force_authenticate(self.user)

    def test_short_and_blank_titles_do_not_create_rows(self):
        for title in ["", "   ", "x", "  ab  "]:
            with self.subTest(title=title):
                response = self.client.post("/api/tasks/", {"title": title}, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertIn("title", response.data)
        self.assertEqual(Task.objects.count(), 0)

    def test_title_is_trimmed(self):
        response = self.client.post("/api/tasks/", {"title": "  Valid task  "}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.get().title, "Valid task")

    def test_maximum_title_length(self):
        self.assertEqual(self.client.post("/api/tasks/", {"title": "x" * 120}, format="json").status_code, 201)
        self.assertEqual(self.client.post("/api/tasks/", {"title": "x" * 121}, format="json").status_code, 400)

    def test_past_date_rejected_on_create(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        response = self.client.post("/api/tasks/", {"title": "Valid task", "due_date": yesterday.isoformat()}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("due_date", response.data)
        self.assertFalse(Task.objects.exists())

    def test_today_future_and_null_are_accepted(self):
        today = timezone.localdate()
        for due_date in [today.isoformat(), (today + timedelta(days=1)).isoformat(), None]:
            with self.subTest(due_date=due_date):
                response = self.client.post("/api/tasks/", {"title": "Valid task", "due_date": due_date}, format="json")
                self.assertEqual(response.status_code, 201)

    def test_malformed_date_rejected(self):
        response = self.client.post("/api/tasks/", {"title": "Valid task", "due_date": "not-a-date"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_overdue_task_status_patch_preserves_existing_date(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        task = Task.objects.create(owner=self.user, title="Overdue task", due_date=yesterday)
        response = self.client.patch(f"/api/tasks/{task.pk}/", {"status": "done"}, format="json")
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.due_date, yesterday)
        self.assertEqual(task.status, "done")

    def test_invalid_patch_is_atomic(self):
        task = Task.objects.create(owner=self.user, title="Original title")
        response = self.client.patch(f"/api/tasks/{task.pk}/", {"title": "x", "status": "done"}, format="json")
        self.assertEqual(response.status_code, 400)
        task.refresh_from_db()
        self.assertEqual(task.title, "Original title")
        self.assertEqual(task.status, "todo")

    def test_new_past_date_rejected_on_patch(self):
        task = Task.objects.create(owner=self.user, title="Valid task")
        yesterday = timezone.localdate() - timedelta(days=1)
        response = self.client.patch(f"/api/tasks/{task.pk}/", {"due_date": yesterday.isoformat()}, format="json")
        self.assertEqual(response.status_code, 400)
        task.refresh_from_db()
        self.assertIsNone(task.due_date)

    def test_due_date_can_be_cleared(self):
        task = Task.objects.create(owner=self.user, title="Valid task", due_date=timezone.localdate())
        response = self.client.patch(f"/api/tasks/{task.pk}/", {"due_date": None}, format="json")
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertIsNone(task.due_date)

    def test_unchanged_overdue_date_can_be_echoed_on_patch(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        task = Task.objects.create(owner=self.user, title="Overdue task", due_date=yesterday)
        response = self.client.patch(
            f"/api/tasks/{task.pk}/",
            {"due_date": yesterday.isoformat(), "status": "done"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.due_date, yesterday)
        self.assertEqual(task.status, "done")

    def test_unchanged_overdue_date_can_be_echoed_on_put(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        task = Task.objects.create(owner=self.user, title="Overdue task", due_date=yesterday)
        response = self.client.put(
            f"/api/tasks/{task.pk}/",
            {"title": "Overdue task", "due_date": yesterday.isoformat(), "status": "done"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.due_date, yesterday)
        self.assertEqual(task.status, "done")

    def test_changing_existing_overdue_date_to_another_past_date_is_rejected(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        earlier = yesterday - timedelta(days=1)
        task = Task.objects.create(owner=self.user, title="Overdue task", due_date=yesterday)
        response = self.client.patch(
            f"/api/tasks/{task.pk}/",
            {"due_date": earlier.isoformat(), "status": "done"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        task.refresh_from_db()
        self.assertEqual(task.due_date, yesterday)
        self.assertEqual(task.status, "todo")

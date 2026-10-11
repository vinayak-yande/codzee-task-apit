from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from tasks.models import Task

class BaselineTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="alice")
        self.client.force_authenticate(self.user)

    def test_create_uses_authenticated_owner(self):
        response = self.client.post("/api/tasks/", {"title": "Write regression tests"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.get().owner, self.user)

    def test_anonymous_request_rejected(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/tasks/").status_code, 401)

    def test_own_task_crud(self):
        task = Task.objects.create(owner=self.user, title="Prepare demo")
        url = f"/api/tasks/{task.pk}/"
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.patch(url, {"status": "done"}, format="json")
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "done")
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Task.objects.exists())

    def test_invalid_status_rejected(self):
        response = self.client.post("/api/tasks/", {"title": "Valid title", "status": "unknown"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Task.objects.exists())

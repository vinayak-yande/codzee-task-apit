from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from tasks.models import Task

class OwnershipTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username="alice")
        self.bob = User.objects.create_user(username="bob")
        self.own_task = Task.objects.create(owner=self.alice, title="Alice task")
        self.other_task = Task.objects.create(owner=self.bob, title="Bob task")
        self.client.force_authenticate(self.alice)

    def test_list_contains_only_owned_tasks(self):
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, 200)
        rows = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertEqual([row["id"] for row in rows], [self.own_task.pk])

    def test_other_users_task_is_not_visible(self):
        self.assertEqual(self.client.get(f"/api/tasks/{self.other_task.pk}/").status_code, 404)

    def test_other_users_task_cannot_be_patched(self):
        response = self.client.patch(f"/api/tasks/{self.other_task.pk}/", {"title": "Changed title"}, format="json")
        self.assertEqual(response.status_code, 404)
        self.other_task.refresh_from_db()
        self.assertEqual(self.other_task.title, "Bob task")

    def test_other_users_task_cannot_be_replaced(self):
        response = self.client.put(f"/api/tasks/{self.other_task.pk}/", {"title": "Changed title", "status": "done"}, format="json")
        self.assertEqual(response.status_code, 404)
        self.other_task.refresh_from_db()
        self.assertEqual(self.other_task.status, "todo")

    def test_other_users_task_cannot_be_deleted(self):
        self.assertEqual(self.client.delete(f"/api/tasks/{self.other_task.pk}/").status_code, 404)
        self.assertTrue(Task.objects.filter(pk=self.other_task.pk).exists())

    def test_forged_owner_ignored_on_creation(self):
        response = self.client.post("/api/tasks/", {"title": "New task", "owner": self.bob.pk}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.get(pk=response.data["id"]).owner, self.alice)

    def test_owner_cannot_be_transferred_via_patch(self):
        response = self.client.patch(f"/api/tasks/{self.own_task.pk}/", {"owner": self.bob.pk}, format="json")
        self.assertEqual(response.status_code, 200)
        self.own_task.refresh_from_db()
        self.assertEqual(self.own_task.owner, self.alice)

    def test_staff_user_is_also_isolated(self):
        self.alice.is_staff = True
        self.alice.save(update_fields=["is_staff"])
        self.assertEqual(self.client.get(f"/api/tasks/{self.other_task.pk}/").status_code, 404)

    def test_anonymous_crud_rejected(self):
        self.client.force_authenticate(None)
        url = f"/api/tasks/{self.own_task.pk}/"
        for method, target in [("get", "/api/tasks/"), ("get", url), ("post", "/api/tasks/"), ("put", url), ("patch", url), ("delete", url)]:
            with self.subTest(method=method, url=target):
                response = getattr(self.client, method)(target)
                self.assertEqual(response.status_code, 401)

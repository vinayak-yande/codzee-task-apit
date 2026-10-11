from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APITestCase
from tasks.models import Task

class PerformanceTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="alice")
        self.client.force_authenticate(self.user)

    def create_tasks(self, count):
        Task.objects.bulk_create([Task(owner=self.user, title=f"Task {i:03d}") for i in range(count)])

    def test_default_pagination_and_second_page(self):
        self.create_tasks(25)
        first = self.client.get("/api/tasks/")
        second = self.client.get("/api/tasks/?page=2")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["count"], 25)
        self.assertEqual(len(first.data["results"]), 20)
        self.assertIsNotNone(first.data["next"])
        self.assertEqual(len(second.data["results"]), 5)
        self.assertIsNone(second.data["next"])

    def test_maximum_page_size(self):
        self.create_tasks(105)
        response = self.client.get("/api/tasks/?page_size=1000")
        self.assertEqual(len(response.data["results"]), 100)
        self.assertEqual(response.data["count"], 105)

    def test_custom_page_size(self):
        self.create_tasks(10)
        response = self.client.get("/api/tasks/?page_size=3")
        self.assertEqual(len(response.data["results"]), 3)

    def test_invalid_page_size_falls_back_to_default(self):
        self.create_tasks(25)
        for value in ["0", "-1", "invalid"]:
            with self.subTest(value=value):
                response = self.client.get("/api/tasks/", {"page_size": value})
                self.assertEqual(len(response.data["results"]), 20)

    def test_invalid_or_out_of_range_page(self):
        self.create_tasks(2)
        for value in ["0", "-1", "invalid", "99"]:
            with self.subTest(value=value):
                self.assertEqual(self.client.get("/api/tasks/", {"page": value}).status_code, 404)

    def test_status_filter(self):
        Task.objects.create(owner=self.user, title="Pending task")
        done = Task.objects.create(owner=self.user, title="Finished task", status="done")
        response = self.client.get("/api/tasks/?status=done")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], done.pk)

    def test_trimmed_case_insensitive_title_search(self):
        match = Task.objects.create(owner=self.user, title="Write Django tests")
        Task.objects.create(owner=self.user, title="Write documentation")
        response = self.client.get("/api/tasks/", {"search": "  DJANGO  "})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], match.pk)

    def test_invalid_filter_inputs_return_400(self):
        for params in [{"status": "invalid"}, {"status": ""}, {"ordering": "owner__password"}, {"search": "x" * 129}]:
            with self.subTest(params=params):
                self.assertEqual(self.client.get("/api/tasks/", params).status_code, 400)

    def test_tied_timestamps_are_stable_across_pages(self):
        self.create_tasks(25)
        Task.objects.all().update(created_at=timezone.now())
        expected = list(Task.objects.order_by("-pk").values_list("pk", flat=True))
        first = self.client.get("/api/tasks/").data["results"]
        second = self.client.get("/api/tasks/?page=2").data["results"]
        self.assertEqual([row["id"] for row in first + second], expected)

    def test_title_ordering_uses_pk_tie_breaker(self):
        tasks = [Task.objects.create(owner=self.user, title="Same title") for _ in range(3)]
        response = self.client.get("/api/tasks/?ordering=title")
        self.assertEqual([row["id"] for row in response.data["results"]], [task.pk for task in tasks])

    def test_empty_list_has_paginated_envelope(self):
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])
        self.assertIsNone(response.data["next"])

    def test_detail_ignores_list_only_filters(self):
        task = Task.objects.create(owner=self.user, title="Pending task")
        response = self.client.get(f"/api/tasks/{task.pk}/?status=done&ordering=invalid")
        self.assertEqual(response.status_code, 200)

    def test_owner_serialization_has_constant_query_count(self):
        self.create_tasks(1)
        with CaptureQueriesContext(connection) as single:
            first = self.client.get("/api/tasks/")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["results"][0]["owner_username"], "alice")
        self.create_tasks(19)
        with CaptureQueriesContext(connection) as many:
            response = self.client.get("/api/tasks/")
        self.assertEqual(len(response.data["results"]), 20)
        self.assertEqual(len(single), 2)  # COUNT + joined page SELECT
        self.assertEqual(len(many), len(single))

from rest_framework.exceptions import ValidationError
from .pagination import TaskPagination
from rest_framework.viewsets import ModelViewSet
from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    pagination_class = TaskPagination

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)

    def filter_queryset(self, queryset):
        # Always join owners, including on detail responses. List filters should
        # not accidentally alter detail lookup semantics.
        queryset = super().filter_queryset(queryset).select_related("owner")
        if self.action != "list":
            return queryset

        params = self.request.query_params
        status = params.get("status")
        if status is not None:
            if status not in Task.Status.values:
                raise ValidationError({"status": "Choose todo, in_progress, or done."})
            queryset = queryset.filter(status=status)

        search = params.get("search", "").strip()
        if len(search) > 128:
            raise ValidationError({"search": "Search must not exceed 128 characters."})
        if search:
            queryset = queryset.filter(title__icontains=search)

        ordering = params.get("ordering", "-created_at")
        if ordering not in {"created_at", "-created_at", "title", "-title"}:
            raise ValidationError({"ordering": "Choose created_at, -created_at, title, or -title."})
        tie_breaker = "-pk" if ordering.startswith("-") else "pk"
        return queryset.order_by(ordering, tie_breaker)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

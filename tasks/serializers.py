from django.utils import timezone
from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Task
        fields = ["id", "owner", "owner_username", "title", "description", "status", "due_date", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]



    def validate_title(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("Title must contain at least three characters.")
        return value

    def validate_due_date(self, value):
        # Field validators run only for supplied fields during a partial update.
        unchanged = self.instance is not None and value == self.instance.due_date
        if value is not None and not unchanged and value < timezone.localdate():
            raise serializers.ValidationError("Due date cannot be before today.")
        return value

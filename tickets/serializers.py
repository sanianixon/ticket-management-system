from rest_framework import serializers
from .models import Project, Ticket, Comment, TicketHistory

class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)

    class Meta:
        model = Ticket
        fields = "__all__"

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get("status", old_status)

        updated_ticket = super().update(instance, validated_data)

        if old_status != new_status:
            TicketHistory.objects.create(
                ticket=updated_ticket,
                old_status=old_status,
                new_status=new_status,
                changed_by=updated_ticket.created_by
            )

        return updated_ticket

class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = '__all__'

class TicketHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = TicketHistory
        fields = '__all__'

from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "role", "phone_number"]
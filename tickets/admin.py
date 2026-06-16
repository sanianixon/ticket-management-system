from django.contrib import admin
from .models import Project, Ticket, Comment, TicketHistory


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_by", "created_at")
    search_fields = ("name", "description")
    list_filter = ("created_at",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "project", "status", "priority", "assigned_to", "created_at")
    search_fields = ("title", "description")
    list_filter = ("status", "priority", "project", "created_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "author", "created_at")
    search_fields = ("message",)
    list_filter = ("created_at",)


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "old_status", "new_status", "changed_by", "changed_at")
    list_filter = ("old_status", "new_status", "changed_at")


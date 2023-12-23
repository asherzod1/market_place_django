from django.contrib import admin
from announcement.models import Announcement, Transports, Like, Comment


# Register your models here.
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display_links = ["id"]
    list_display = ["id", "title", "user"]


@admin.register(Transports)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display_links = ["id"]
    list_display = ["id", "name", "type"]


@admin.register(Like)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display_links = ["id"]
    list_display = ["id", "created", "user", "announcement"]


@admin.register(Comment)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display_links = ["id"]
    list_display = ["id", "created", "user", "announcement"]
